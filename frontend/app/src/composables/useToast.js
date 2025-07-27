/**
 * Simple toast notification composable
 * Provides a basic toast notification system using browser alerts
 * TODO: Replace with a proper toast library like vue-toastification
 */

export function useToast() {
  const showToast = (message, type = "info") => {
    // For now, use console and alert for notifications
    // In a production app, you'd want to use a proper toast library
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Use alert for important messages (errors)
    if (type === "error") {
      alert(`Error: ${message}`);
    } else if (type === "success") {
      // For success messages, just log to console for now
      // In production, you'd show a green toast notification
      console.log(`✅ ${message}`);
    }
  };

  return {
    showToast,
  };
}
