/// Note model.
class Note {
  final String id;
  final String title;
  final String content;
  final List<String> tags;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Note({
    required this.id,
    required this.title,
    required this.content,
    required this.tags,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Note.fromJson(Map<String, dynamic> json) {
    return Note(
      id: json['id'] as String,
      title: json['title'] as String,
      content: json['content'] as String,
      tags: (json['tags'] as List<dynamic>).cast<String>(),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'content': content,
      'tags': tags,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

/// Note creation payload.
class NoteCreate {
  final String title;
  final String content;
  final List<String> tags;

  const NoteCreate({
    required this.title,
    this.content = '',
    this.tags = const [],
  });

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'content': content,
      'tags': tags,
    };
  }
}
