## 2024-05-23 - [Inaccessible Feedback Controls]
**Learning:** Icon-only buttons without accessible labels exclude screen reader users from providing feedback on AI responses.
**Action:** Always pair `lucide-react` icons with `aria-label` for interactive elements, not just `title`.

## 2024-05-23 - [Scope Containment]
**Learning:** Avoid "fixing" lint configs or dependencies in a UX PR. It bloats the diff and distracts from the actual improvement.
**Action:** Stick strictly to the component files unless explicitly asked to upgrade tooling.

## 2024-05-23 - Visual Polish for Keyboard Shortcuts
**Learning:** Users respond well to visual keyboard shortcuts styled with `<kbd>` tags. It makes the interface feel more "pro" and "finished" compared to plain text instructions. Using `bg-muted` and `font-mono` creates a consistent look that fits the design system.
**Action:** When adding helper text that involves key presses, always use the standard `<kbd>` component/classes: `inline-flex h-5 items-center rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground`.
