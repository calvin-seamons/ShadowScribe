## 2024-05-23 - [Inaccessible Feedback Controls]
**Learning:** Icon-only buttons without accessible labels exclude screen reader users from providing feedback on AI responses.
**Action:** Always pair `lucide-react` icons with `aria-label` for interactive elements, not just `title`.

## 2024-05-23 - [Scope Containment]
**Learning:** Avoid "fixing" lint configs or dependencies in a UX PR. It bloats the diff and distracts from the actual improvement.
**Action:** Stick strictly to the component files unless explicitly asked to upgrade tooling.

## 2024-05-24 - [Accessible Helper Text]
**Learning:** Form inputs with visible helper text (like keyboard shortcuts) are often skipped by screen readers unless explicitly associated.
**Action:** Use `aria-describedby` on the input to point to the helper text container's ID.
