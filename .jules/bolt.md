## 2024-05-23 - [Optimizing Store Subscriptions in List Components]
**Learning:** Subscribing to the entire Zustand store in list components (like `MessageBubble`) causes massive re-renders because any state update triggers all list items to update. Even if the data they need hasn't changed.
**Action:** Always use granular selectors in list components: `useStore(state => state.specificData)`. Wrap list items in `React.memo` and ensure selectors return stable references (e.g., use a constant for empty arrays).

## 2024-05-24 - [Isolating High-Frequency Updates]
**Learning:** Components subscribing to high-frequency data (like streaming text tokens) trigger re-renders on every update. If this component is a large list container (`MessageList`), the entire list reconciles on every token, causing jank.
**Action:** Extract the high-frequency UI into a dedicated leaf component (`StreamingMessage`) that subscribes to the fast-changing data. The parent list should only subscribe to stable data (committed messages) to avoid unnecessary re-renders.
