## 2024-05-23 - [Inaccessible Feedback Controls]
**Learning:** Icon-only buttons without accessible labels exclude screen reader users from providing feedback on AI responses.
**Action:** Always pair `lucide-react` icons with `aria-label` for interactive elements, not just `title`.

## 2024-05-23 - [Scope Containment]
**Learning:** Avoid "fixing" lint configs or dependencies in a UX PR. It bloats the diff and distracts from the actual improvement.
**Action:** Stick strictly to the component files unless explicitly asked to upgrade tooling.

## 2025-05-02 - [Accessible Input Labels]
**Learning:** Even with placeholders, form inputs like textareas need explicit `aria-label` or `label` elements for screen readers. Placeholders are not a substitute for labels.
**Action:** Always add `aria-label` to inputs that don't have a visible `<label>` element.
