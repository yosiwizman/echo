import os
from enum import Enum
from typing import Optional, Tuple, Any

import numpy as np
import requests
from fastapi import HTTPException
from pydub import AudioSegment

from database import redis_db

# ---------------------------------------------------------------------------
# Lazy VAD model initialization (avoid network downloads at import time)
# Default (CI/dev): VAD model is optional; downloads only when VAD is invoked.
# Set ECHO_DISABLE_MODEL_DOWNLOADS=1 to prevent downloads entirely.
# ---------------------------------------------------------------------------
_DISABLE_DOWNLOADS = os.environ.get('ECHO_DISABLE_MODEL_DOWNLOADS', '').lower() in ('1', 'true')

_vad_model: Optional[Any] = None
_vad_utils: Optional[Tuple] = None
_vad_loaded: bool = False


def _get_vad_model_and_utils():
    """Return the silero-vad model and utils, loading lazily on first call.

    Raises:
        RuntimeError: If downloads are disabled and model is not cached.
    """
    global _vad_model, _vad_utils, _vad_loaded

    if not _vad_loaded:
        import torch
        torch.set_num_threads(1)
        torch.hub.set_dir('pretrained_models')

        if _DISABLE_DOWNLOADS:
            # Check if model is already cached
            cache_dir = os.path.join('pretrained_models', 'snakers4_silero-vad_master')
            if not os.path.exists(cache_dir):
                raise RuntimeError(
                    "VAD model not cached and ECHO_DISABLE_MODEL_DOWNLOADS=1. "
                    "Run locally first to cache the model, or unset the flag."
                )

        _vad_model, _vad_utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            trust_repo=True
        )
        _vad_loaded = True

    return _vad_model, _vad_utils


def _get_vad_model():
    """Return the VAD model."""
    model, _ = _get_vad_model_and_utils()
    return model


def _get_vad_utils():
    """Return the VAD utility functions."""
    _, utils = _get_vad_model_and_utils()
    return utils


def _get_speech_timestamps_func():
    """Return the get_speech_timestamps function."""
    utils = _get_vad_utils()
    return utils[0]


def _get_read_audio_func():
    """Return the read_audio function."""
    utils = _get_vad_utils()
    return utils[2]


def _get_vad_iterator_class():
    """Return the VADIterator class."""
    utils = _get_vad_utils()
    return utils[3]


class SpeechState(str, Enum):
    speech_found = 'speech_found'
    no_speech = 'no_speech'


def is_speech_present(data, vad_iterator, window_size_samples=256):
    data_int16 = np.frombuffer(data, dtype=np.int16)
    data_float32 = data_int16.astype(np.float32) / 32768.0
    has_start, has_end = False, False

    for i in range(0, len(data_float32), window_size_samples):
        chunk = data_float32[i : i + window_size_samples]
        if len(chunk) < window_size_samples:
            break
        speech_dict = vad_iterator(chunk, return_seconds=False)
        if speech_dict:
            # print(speech_dict)
            vad_iterator.reset_states()
            return SpeechState.speech_found

            # if not has_start and 'start' in speech_dict:
            #     has_start = True
            #
            # if not has_end and 'end' in speech_dict:
            #     has_end = True

    # if has_start:
    #     return SpeechState.speech_found
    # elif has_end:
    #     return SpeechState.no_speech
    vad_iterator.reset_states()
    return SpeechState.no_speech


def is_audio_empty(file_path, sample_rate=8000):
    read_audio = _get_read_audio_func()
    get_speech_timestamps = _get_speech_timestamps_func()
    model = _get_vad_model()
    wav = read_audio(file_path)
    timestamps = get_speech_timestamps(wav, model, sampling_rate=sample_rate)
    if len(timestamps) == 1:
        prob_not_speech = ((timestamps[0]['end'] / 1000) - (timestamps[0]['start'] / 1000)) < 1
        return prob_not_speech
    return len(timestamps) == 0


def vad_is_empty(file_path, return_segments: bool = False, cache: bool = False):
    """Uses vad_modal/vad.py deployment (Best quality)"""
    caching_key = f'vad_is_empty:{file_path}'
    if cache:
        if exists := redis_db.get_generic_cache(caching_key):
            if return_segments:
                return exists
            return len(exists) == 0

    with open(file_path, 'rb') as file:
        files = {'file': (file_path.split('/')[-1], file, 'audio/wav')}
        response = requests.post(os.getenv('HOSTED_VAD_API_URL'), files=files)
        response.raise_for_status()  # Raise exception for HTTP errors
        segments = response.json()
        if cache:
            redis_db.set_generic_cache(caching_key, segments, ttl=60 * 60 * 24)
        if return_segments:
            return segments
        print('vad_is_empty', len(segments) == 0)
        return len(segments) == 0


def apply_vad_for_speech_profile(file_path: str):
    print('apply_vad_for_speech_profile', file_path)
    voice_segments = vad_is_empty(file_path, return_segments=True)
    if len(voice_segments) == 0:  # TODO: front error on post-processing, audio sent is bad.
        raise HTTPException(status_code=400, detail="Audio is empty")
    joined_segments = []
    for i, segment in enumerate(voice_segments):
        if joined_segments and (segment['start'] - joined_segments[-1]['end']) < 1:
            joined_segments[-1]['end'] = segment['end']
        else:
            joined_segments.append(segment)

    # Load audio file once instead of repeatedly in the loop
    full_audio = AudioSegment.from_wav(file_path)

    try:
        # trim silence out of file_path, but leave 1 sec of silence within chunks
        trimmed_aseg = AudioSegment.empty()
        for i, segment in enumerate(joined_segments):
            start = segment['start'] * 1000
            end = segment['end'] * 1000
            trimmed_aseg += full_audio[start:end]
            if i < len(joined_segments) - 1:
                trimmed_aseg += full_audio[end : end + 1000]

        # file_path.replace('.wav', '-cleaned.wav')
        trimmed_aseg.export(file_path, format="wav")
    finally:
        # Explicitly free memory
        del full_audio
        del trimmed_aseg
