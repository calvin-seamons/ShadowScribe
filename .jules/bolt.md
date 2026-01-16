## 2024-05-23 - [Optimizing Store Subscriptions in List Components]
**Learning:** Subscribing to the entire Zustand store in list components (like `MessageBubble`) causes massive re-renders because any state update triggers all list items to update. Even if the data they need hasn't changed.
**Action:** Always use granular selectors in list components: `useStore(state => state.specificData)`. Wrap list items in `React.memo` and ensure selectors return stable references (e.g., use a constant for empty arrays).

## 2024-05-24 - [Isolating High-Frequency Streaming Updates]
**Learning:** In chat interfaces, subscribing the main message list to the streaming state (`currentStreamingMessage`) triggers a re-render of the entire list for every token received.
**Action:** Isolate the streaming message into a dedicated component (`StreamingMessage`) that subscribes to the high-frequency state. Use `store.subscribe` in `useEffect` for side effects like auto-scrolling to avoid re-rendering the parent container.
