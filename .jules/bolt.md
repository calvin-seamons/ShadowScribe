## 2024-05-23 - [Optimizing Store Subscriptions in List Components]
**Learning:** Subscribing to the entire Zustand store in list components (like `MessageBubble`) causes massive re-renders because any state update triggers all list items to update. Even if the data they need hasn't changed.
**Action:** Always use granular selectors in list components: `useStore(state => state.specificData)`. Wrap list items in `React.memo` and ensure selectors return stable references (e.g., use a constant for empty arrays).
