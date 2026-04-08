# app/agents/notes_agent.py
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Note
import re


class NotesAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session

    async def process_notes_query(self, query: str) -> Dict[str, Any]:
        """Process note-related queries"""
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in ["create", "add", "new", "take"]):
            return await self.create_note(query)
        elif any(keyword in query_lower for keyword in ["list", "show", "view", "all"]):
            return await self.list_notes()
        elif any(keyword in query_lower for keyword in ["search", "find"]):
            return await self.search_notes(query)
        elif any(keyword in query_lower for keyword in ["delete", "remove"]):
            return await self.delete_note(query)
        elif "pin" in query_lower:
            return await self.pin_note(query)
        else:
            return await self.get_notes_summary()

    async def create_note(self, query: str) -> Dict[str, Any]:
        """Create a new note"""
        # Extract title
        title_match = re.search(
            r"(?:note)[:\s]+(.+?)(?:about|with|$)", query, re.IGNORECASE
        )
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = (
                query.replace("create", "")
                .replace("note", "")
                .replace("add", "")
                .replace("take", "")
                .strip()
            )
            if len(title) > 50:
                title = title[:47] + "..."

        if not title:
            title = f"Note {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Extract content
        content = query
        if "about" in query.lower():
            content_match = re.search(r"about\s+(.+?)(?:$)", query, re.IGNORECASE)
            if content_match:
                content = content_match.group(1).strip()

        # Extract tags
        tags = []
        tag_matches = re.findall(r"#(\w+)", query)
        if tag_matches:
            tags = tag_matches

        note = Note(user_id=self.user_id, title=title[:200], content=content, tags=tags)

        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)

        return {
            "status": "success",
            "response": f"📝 Note created: '{title}'",
            "note": {"id": note.id, "title": note.title, "tags": note.tags},
        }

    async def list_notes(self) -> Dict[str, Any]:
        """List all notes"""
        notes = (
            self.db.query(Note)
            .filter(Note.user_id == self.user_id)
            .order_by(Note.is_pinned.desc(), Note.updated_at.desc())
            .limit(10)
            .all()
        )

        if not notes:
            return {
                "status": "success",
                "response": "📝 No notes yet. Create your first note!",
            }

        note_list = []
        for i, note in enumerate(notes, 1):
            pin_icon = "📌 " if note.is_pinned else ""
            tag_str = f" #{note.tags[0]}" if note.tags else ""
            note_list.append(f"{i}. {pin_icon}{note.title}{tag_str}")

        response = f"📝 Recent Notes ({len(notes)}):\n\n" + "\n".join(note_list)

        return {
            "status": "success",
            "response": response,
            "notes": [{"id": n.id, "title": n.title} for n in notes],
        }

    async def search_notes(self, query: str) -> Dict[str, Any]:
        """Search notes"""
        search_term = (
            query.replace("search", "").replace("find", "").replace("note", "").strip()
        )

        if not search_term:
            return {"status": "error", "message": "Please provide a search term"}

        notes = (
            self.db.query(Note)
            .filter(
                Note.user_id == self.user_id,
                (
                    Note.title.ilike(f"%{search_term}%")
                    | Note.content.ilike(f"%{search_term}%")
                ),
            )
            .order_by(Note.updated_at.desc())
            .all()
        )

        if not notes:
            return {
                "status": "success",
                "response": f"No notes found matching '{search_term}'",
            }

        note_list = []
        for note in notes[:10]:
            preview = (
                note.content[:80] + "..." if len(note.content) > 80 else note.content
            )
            note_list.append(f"• {note.title}\n  {preview}\n")

        response = (
            f"Found {len(notes)} note(s) matching '{search_term}':\n\n"
            + "\n".join(note_list)
        )

        return {
            "status": "success",
            "response": response,
            "notes": [{"id": n.id, "title": n.title} for n in notes],
        }

    async def delete_note(self, query: str) -> Dict[str, Any]:
        """Delete a note"""
        note_id_match = re.search(r"(\d+)", query)
        if note_id_match:
            note_id = int(note_id_match.group(1))
            note = (
                self.db.query(Note)
                .filter(Note.id == note_id, Note.user_id == self.user_id)
                .first()
            )

            if note:
                title = note.title
                self.db.delete(note)
                self.db.commit()
                return {"status": "success", "response": f"🗑️ Note deleted: '{title}'"}

        return {
            "status": "error",
            "message": "Note not found. Please provide a valid note ID.",
        }

    async def pin_note(self, query: str) -> Dict[str, Any]:
        """Pin/unpin a note"""
        note_id_match = re.search(r"(\d+)", query)
        if note_id_match:
            note_id = int(note_id_match.group(1))
            note = (
                self.db.query(Note)
                .filter(Note.id == note_id, Note.user_id == self.user_id)
                .first()
            )

            if note:
                note.is_pinned = not note.is_pinned
                self.db.commit()
                action = "pinned" if note.is_pinned else "unpinned"
                return {
                    "status": "success",
                    "response": f"📌 Note {action}: '{note.title}'",
                }

        return {
            "status": "error",
            "message": "Note not found. Please provide a valid note ID.",
        }

    async def get_notes_summary(self) -> Dict[str, Any]:
        """Get notes summary"""
        total_notes = self.db.query(Note).filter(Note.user_id == self.user_id).count()
        # Fixed: Changed from '== True' to direct boolean check
        pinned_notes = (
            self.db.query(Note)
            .filter(
                Note.user_id == self.user_id,
                Note.is_pinned,  # Fixed: removed '== True' comparison
            )
            .count()
        )

        # Get tags statistics
        all_notes = self.db.query(Note).filter(Note.user_id == self.user_id).all()
        tag_counts = {}
        for note in all_notes:
            for tag in note.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        response = "📊 Notes Summary:\n\n"
        response += f"📝 Total Notes: {total_notes}\n"
        response += f"📌 Pinned Notes: {pinned_notes}\n"

        if top_tags:
            response += "\n🏷️ Top Tags:\n"
            for tag, count in top_tags:
                response += f"   • #{tag}: {count} note(s)\n"

        return {
            "status": "success",
            "response": response,
            "summary": {
                "total": total_notes,
                "pinned": pinned_notes,
                "top_tags": dict(top_tags),
            },
        }
