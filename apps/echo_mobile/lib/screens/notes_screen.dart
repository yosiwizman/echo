import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:echo_mobile/models/note.dart';
import 'package:echo_mobile/services/api_service.dart';
import 'package:echo_mobile/screens/create_note_screen.dart';

/// Notes screen showing list of notes.
class NotesScreen extends StatefulWidget {
  const NotesScreen({super.key});

  @override
  State<NotesScreen> createState() => _NotesScreenState();
}

class _NotesScreenState extends State<NotesScreen> {
  List<Note>? _notes;
  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadNotes();
  }

  Future<void> _loadNotes() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final api = context.read<ApiService>();
      final notes = await api.getNotes();
      setState(() {
        _notes = notes;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _deleteNote(Note note) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Note'),
        content: Text('Are you sure you want to delete "${note.title}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        final api = context.read<ApiService>();
        await api.deleteNote(note.id);
        _loadNotes();
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to delete: $e')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notes'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadNotes,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final created = await Navigator.push<bool>(
            context,
            MaterialPageRoute(
              builder: (context) => const CreateNoteScreen(),
            ),
          );
          if (created == true) {
            _loadNotes();
          }
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading && _notes == null) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null && _notes == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text('Failed to load notes'),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: _loadNotes,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_notes == null || _notes!.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.note_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.outline,
            ),
            const SizedBox(height: 16),
            Text(
              'No notes yet',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Tap + to create your first note',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadNotes,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _notes!.length,
        itemBuilder: (context, index) {
          final note = _notes![index];
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              title: Text(
                note.title,
                style: const TextStyle(fontWeight: FontWeight.w500),
              ),
              subtitle: note.content.isNotEmpty
                  ? Text(
                      note.content,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    )
                  : null,
              trailing: IconButton(
                icon: const Icon(Icons.delete_outline),
                onPressed: () => _deleteNote(note),
              ),
              onTap: () {
                // TODO: Navigate to note detail in future
              },
            ),
          );
        },
      ),
    );
  }
}
