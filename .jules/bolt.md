## 2024-05-23 - [Optimizing Store Subscriptions in List Components]
**Learning:** Subscribing to the entire Zustand store in list components (like `MessageBubble`) causes massive re-renders because any state update triggers all list items to update. Even if the data they need hasn't changed.
**Action:** Always use granular selectors in list components: `useStore(state => state.specificData)`. Wrap list items in `React.memo` and ensure selectors return stable references (e.g., use a constant for empty arrays).

## 2024-05-24 - [Isolating High-Frequency Streaming Updates]
**Learning:** Subscribing to streaming text updates (`currentStreamingMessage`) in the main list component (`MessageList`) triggers a full list re-render on every token, which is expensive.
**Action:** Extract streaming text rendering into a dedicated component (`StreamingMessage`) that subscribes *only* to the streaming text. The parent component should conditionally render it based on `isStreaming` but NOT subscribe to the text content itself.
