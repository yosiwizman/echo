import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:echo_mobile/models/note.dart';

/// Service for communicating with the Echo backend.
class ApiService {
  final String baseUrl;
  final http.Client _client;

  ApiService({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  /// Check backend health.
  Future<Map<String, dynamic>> healthCheck() async {
    final response = await _client.get(Uri.parse('$baseUrl/healthz'));
    _checkResponse(response);
    return json.decode(response.body) as Map<String, dynamic>;
  }

  /// Send a chat message.
  Future<Map<String, dynamic>> chat({
    required String sessionId,
    required String userText,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/chat'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'session_id': sessionId,
        'user_text': userText,
      }),
    );
    _checkResponse(response);
    return json.decode(response.body) as Map<String, dynamic>;
  }

  /// Get all notes.
  Future<List<Note>> getNotes() async {
    final response = await _client.get(Uri.parse('$baseUrl/notes'));
    _checkResponse(response);
    final data = json.decode(response.body) as Map<String, dynamic>;
    final notesList = data['notes'] as List<dynamic>;
    return notesList
        .map((n) => Note.fromJson(n as Map<String, dynamic>))
        .toList();
  }

  /// Get a note by ID.
  Future<Note> getNote(String id) async {
    final response = await _client.get(Uri.parse('$baseUrl/notes/$id'));
    _checkResponse(response);
    return Note.fromJson(json.decode(response.body) as Map<String, dynamic>);
  }

  /// Create a new note.
  Future<Note> createNote(NoteCreate note) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/notes'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(note.toJson()),
    );
    _checkResponse(response);
    return Note.fromJson(json.decode(response.body) as Map<String, dynamic>);
  }

  /// Delete a note.
  Future<void> deleteNote(String id) async {
    final response = await _client.delete(Uri.parse('$baseUrl/notes/$id'));
    if (response.statusCode != 204) {
      _checkResponse(response);
    }
  }

  void _checkResponse(http.Response response) {
    if (response.statusCode >= 400) {
      throw ApiException(
        statusCode: response.statusCode,
        message: response.body,
      );
    }
  }
}

/// Exception thrown when API calls fail.
class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException({required this.statusCode, required this.message});

  @override
  String toString() => 'ApiException($statusCode): $message';
}
