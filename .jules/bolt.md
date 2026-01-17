## 2024-05-23 - [Optimizing Store Subscriptions in List Components]
**Learning:** Subscribing to the entire Zustand store in list components (like `MessageBubble`) causes massive re-renders because any state update triggers all list items to update. Even if the data they need hasn't changed.
**Action:** Always use granular selectors in list components: `useStore(state => state.specificData)`. Wrap list items in `React.memo` and ensure selectors return stable references (e.g., use a constant for empty arrays).

## 2024-05-24 - [Optimizing Streaming Text Rendering]
**Learning:** Even with granular selectors in list components (`MessageList`), if the parent component (`ChatContainer`) subscribes to the full store, it will re-render the list on every update (like streaming tokens).
**Action:** Isolate high-frequency updates (streaming text) into a dedicated component (`StreamingMessage`) and wrap the list component in `React.memo()`. This prevents the expensive list reconciliation even if the parent re-renders.
