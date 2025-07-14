<template>
  <div
    class="security-dashboard bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6"
  >
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
        Security Dashboard
      </h2>
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 rounded-full" :class="securityStatusColor"></div>
          <span class="text-sm text-gray-600 dark:text-gray-400">{{
            securityStatusText
          }}</span>
        </div>
        <button
          @click="refreshSecurityData"
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {{ loading ? "Loading..." : "Refresh" }}
        </button>
      </div>
    </div>

    <!-- Security Score Overview -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div
        class="bg-gradient-to-r from-blue-500 to-blue-600 p-6 rounded-lg text-white"
      >
        <div class="flex items-center justify-between">
          <div>
            <div class="text-3xl font-bold">{{ securityScore }}%</div>
            <div class="text-blue-100">Security Score</div>
          </div>
          <div class="text-4xl opacity-80">🛡️</div>
        </div>
        <div class="mt-2">
          <div class="w-full bg-blue-400 rounded-full h-2">
            <div
              class="bg-white h-2 rounded-full transition-all duration-500"
              :style="{ width: `${securityScore}%` }"
            ></div>
          </div>
        </div>
      </div>

      <div
        class="bg-gradient-to-r from-green-500 to-green-600 p-6 rounded-lg text-white"
      >
        <div class="flex items-center justify-between">
          <div>
            <div class="text-3xl font-bold">{{ activeSessions.length }}</div>
            <div class="text-green-100">Active Sessions</div>
          </div>
          <div class="text-4xl opacity-80">📱</div>
        </div>
        <div class="text-sm text-green-100 mt-2">
          {{ maxSessions - activeSessions.length }} slots available
        </div>
      </div>

      <div
        class="bg-gradient-to-r from-yellow-500 to-yellow-600 p-6 rounded-lg text-white"
      >
        <div class="flex items-center justify-between">
          <div>
            <div class="text-3xl font-bold">{{ securityAlerts.length }}</div>
            <div class="text-yellow-100">Security Alerts</div>
          </div>
          <div class="text-4xl opacity-80">⚠️</div>
        </div>
        <div class="text-sm text-yellow-100 mt-2">
          {{ criticalAlerts.length }} critical
        </div>
      </div>

      <div
        class="bg-gradient-to-r from-purple-500 to-purple-600 p-6 rounded-lg text-white"
      >
        <div class="flex items-center justify-between">
          <div>
            <div class="text-3xl font-bold">{{ auditEvents.length }}</div>
            <div class="text-purple-100">Recent Events</div>
          </div>
          <div class="text-4xl opacity-80">📋</div>
        </div>
        <div class="text-sm text-purple-100 mt-2">Last 24 hours</div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 dark:border-dark-600 mb-6">
      <nav class="-mb-px flex space-x-8">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'py-2 px-1 border-b-2 font-medium text-sm',
            activeTab === tab.id
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300',
          ]"
        >
          {{ tab.name }}
          <span
            v-if="tab.count !== undefined"
            class="ml-2 bg-gray-100 dark:bg-dark-600 text-gray-600 dark:text-gray-300 py-0.5 px-2 rounded-full text-xs"
          >
            {{ tab.count }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Security Overview Tab -->
    <div v-if="activeTab === 'overview'" class="space-y-6">
      <!-- Security Recommendations -->
      <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Security Recommendations
        </h3>
        <div class="space-y-3">
          <div
            v-for="recommendation in securityRecommendations"
            :key="recommendation.id"
            class="flex items-start space-x-3 p-3 rounded border"
            :class="getRecommendationClass(recommendation.priority)"
          >
            <div class="flex-shrink-0 mt-0.5">
              <div
                class="w-2 h-2 rounded-full"
                :class="getRecommendationDotClass(recommendation.priority)"
              ></div>
            </div>
            <div class="flex-1">
              <div class="font-medium text-gray-900 dark:text-white">
                {{ recommendation.title }}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">
                {{ recommendation.description }}
              </div>
              <button
                v-if="recommendation.action"
                @click="executeRecommendation(recommendation)"
                class="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                {{ recommendation.actionText }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Security Events -->
      <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Recent Security Events
        </h3>
        <div class="space-y-3 max-h-64 overflow-y-auto">
          <div
            v-for="event in recentSecurityEvents"
            :key="event.id"
            class="flex items-center justify-between p-3 bg-white dark:bg-dark-800 rounded border"
          >
            <div class="flex items-center space-x-3">
              <div
                class="w-3 h-3 rounded-full"
                :class="getEventSeverityColor(event.severity)"
              ></div>
              <div>
                <div class="font-medium text-gray-900 dark:text-white">
                  {{ formatEventType(event.type) }}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">
                  {{ formatEventTime(event.timestamp) }}
                </div>
              </div>
            </div>
            <button
              @click="showEventDetails(event)"
              class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              Details
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Sessions Tab -->
    <div v-if="activeTab === 'sessions'" class="space-y-6">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Active Sessions
        </h3>
        <button
          @click="terminateAllOtherSessions"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Terminate All Others
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="session in activeSessions"
          :key="session.id"
          class="border border-gray-200 dark:border-dark-600 rounded-lg p-4"
          :class="{ 'ring-2 ring-blue-500': session.id === currentSessionId }"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-2">
              <div class="text-lg">{{ getDeviceIcon(session.deviceType) }}</div>
              <span class="font-medium text-gray-900 dark:text-white">
                {{ session.deviceName || "Unknown Device" }}
              </span>
              <span
                v-if="session.id === currentSessionId"
                class="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded"
              >
                Current
              </span>
            </div>
            <button
              v-if="session.id !== currentSessionId"
              @click="terminateSession(session.id)"
              class="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
            >
              Terminate
            </button>
          </div>

          <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <div class="flex justify-between">
              <span>Location:</span>
              <span>{{ session.location || "Unknown" }}</span>
            </div>
            <div class="flex justify-between">
              <span>IP Address:</span>
              <span>{{ session.ipAddress || "Unknown" }}</span>
            </div>
            <div class="flex justify-between">
              <span>Last Active:</span>
              <span>{{ formatLastActive(session.lastActive) }}</span>
            </div>
            <div class="flex justify-between">
              <span>Created:</span>
              <span>{{ formatSessionTime(session.createdAt) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Audit Log Tab -->
    <div v-if="activeTab === 'audit'" class="space-y-6">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Audit Log
        </h3>
        <div class="flex items-center space-x-4">
          <input
            v-model="auditSearchQuery"
            type="text"
            placeholder="Search audit events..."
            class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
          />
          <select
            v-model="auditFilter"
            class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
          >
            <option value="all">All Events</option>
            <option value="login">Login Events</option>
            <option value="content">Content Events</option>
            <option value="security">Security Events</option>
            <option value="admin">Admin Events</option>
          </select>
          <button
            @click="exportAuditLog"
            class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            Export
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-dark-600">
              <th
                class="text-left py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Timestamp
              </th>
              <th
                class="text-left py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                User
              </th>
              <th
                class="text-left py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Action
              </th>
              <th
                class="text-left py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Details
              </th>
              <th
                class="text-left py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                IP Address
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="event in filteredAuditEvents"
              :key="event.id"
              class="border-b border-gray-100 dark:border-dark-600 hover:bg-gray-50 dark:hover:bg-dark-700"
            >
              <td class="py-3 px-4 text-gray-600 dark:text-gray-300">
                {{ formatAuditTime(event.timestamp) }}
              </td>
              <td class="py-3 px-4 text-gray-900 dark:text-white">
                {{ event.userId || "System" }}
              </td>
              <td class="py-3 px-4">
                <span
                  class="px-2 py-1 text-xs rounded-full"
                  :class="getActionClass(event.action)"
                >
                  {{ formatActionName(event.action) }}
                </span>
              </td>
              <td class="py-3 px-4 text-gray-600 dark:text-gray-300">
                {{ formatEventDetails(event.details) }}
              </td>
              <td class="py-3 px-4 text-gray-600 dark:text-gray-300">
                {{ event.ipAddress || "N/A" }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Privacy Tab -->
    <div v-if="activeTab === 'privacy'" class="space-y-6">
      <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Privacy Settings
        </h3>

        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-900 dark:text-white">
                Data Collection
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">
                Allow collection of usage data for service improvement
              </div>
            </div>
            <input
              v-model="privacySettings.dataCollection"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </div>

          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-900 dark:text-white">
                Analytics
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">
                Enable analytics tracking for personalized experience
              </div>
            </div>
            <input
              v-model="privacySettings.analytics"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </div>

          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-900 dark:text-white">
                Personalized Content
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">
                Show personalized content recommendations
              </div>
            </div>
            <input
              v-model="privacySettings.personalizedContent"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </div>

          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-900 dark:text-white">
                Share Reading Data
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">
                Share reading statistics with other users
              </div>
            </div>
            <input
              v-model="privacySettings.shareReadingData"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </div>

          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-900 dark:text-white">
                Public Profile
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">
                Make your profile visible to other users
              </div>
            </div>
            <input
              v-model="privacySettings.publicProfile"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </div>
        </div>

        <div class="mt-6 flex space-x-4">
          <button
            @click="savePrivacySettings"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Save Settings
          </button>
          <button
            @click="exportUserData"
            class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            Export My Data
          </button>
          <button
            @click="showDeleteDataConfirm = true"
            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Delete My Data
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Data Confirmation Modal -->
    <div
      v-if="showDeleteDataConfirm"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showDeleteDataConfirm = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6"
        >
          <div class="sm:flex sm:items-start">
            <div
              class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900 sm:mx-0 sm:h-10 sm:w-10"
            >
              <svg
                class="h-6 w-6 text-red-600 dark:text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3
                class="text-lg leading-6 font-medium text-gray-900 dark:text-white"
              >
                Delete Account Data
              </h3>
              <div class="mt-2">
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Are you sure you want to delete all your account data? This
                  action cannot be undone and will permanently remove all your
                  reading history, bookmarks, and personal settings.
                </p>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              @click="deleteUserData"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Delete Data
            </button>
            <button
              @click="showDeleteDataConfirm = false"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-700 text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useSecurityStore } from "../stores/security";
import { useAuthStore } from "../stores/auth";

const securityStore = useSecurityStore();
const authStore = useAuthStore();

// Local state
const loading = ref(false);
const activeTab = ref("overview");
const auditSearchQuery = ref("");
const auditFilter = ref("all");
const showDeleteDataConfirm = ref(false);

// Privacy settings (reactive copy)
const privacySettings = ref({ ...securityStore.privacySettings });

// Computed properties
const securityScore = computed(() => securityStore.getSecurityScore);
const activeSessions = computed(() => securityStore.getActiveSessions);
const securityAlerts = computed(() => securityStore.getSecurityAlerts);
const auditEvents = computed(() => securityStore.getRecentAuditEvents(100));

const maxSessions = computed(
  () => securityStore.securitySettings.maxConcurrentSessions,
);
const currentSessionId = computed(() => securityStore.currentSession?.id);

const criticalAlerts = computed(() =>
  securityAlerts.value.filter((alert) => alert.severity === "critical"),
);

const recentSecurityEvents = computed(() =>
  securityStore.securityEvents.slice(0, 10),
);

const securityStatusColor = computed(() => {
  const score = securityScore.value;
  if (score >= 80) return "bg-green-500";
  if (score >= 60) return "bg-yellow-500";
  return "bg-red-500";
});

const securityStatusText = computed(() => {
  const score = securityScore.value;
  if (score >= 80) return "Excellent Security";
  if (score >= 60) return "Good Security";
  if (score >= 40) return "Fair Security";
  return "Poor Security";
});

const securityRecommendations = computed(() => {
  const recommendations = [];

  if (!securityStore.twoFactorEnabled) {
    recommendations.push({
      id: "enable-2fa",
      title: "Enable Two-Factor Authentication",
      description: "Add an extra layer of security to your account",
      priority: "high",
      action: "enable2FA",
      actionText: "Enable 2FA",
    });
  }

  if (securityStore.securitySettings.sessionTimeout > 3600000) {
    recommendations.push({
      id: "reduce-session-timeout",
      title: "Reduce Session Timeout",
      description: "Consider reducing session timeout for better security",
      priority: "medium",
      action: "reduceTimeout",
      actionText: "Update Settings",
    });
  }

  if (activeSessions.value.length > 3) {
    recommendations.push({
      id: "review-sessions",
      title: "Review Active Sessions",
      description:
        "You have multiple active sessions. Review and terminate unused ones.",
      priority: "medium",
      action: "reviewSessions",
      actionText: "Review Sessions",
    });
  }

  if (privacySettings.value.dataCollection && privacySettings.value.analytics) {
    recommendations.push({
      id: "review-privacy",
      title: "Review Privacy Settings",
      description: "Consider limiting data collection for better privacy",
      priority: "low",
      action: "reviewPrivacy",
      actionText: "Review Privacy",
    });
  }

  return recommendations;
});

const tabs = computed(() => [
  { id: "overview", name: "Overview" },
  { id: "sessions", name: "Sessions", count: activeSessions.value.length },
  { id: "audit", name: "Audit Log", count: auditEvents.value.length },
  { id: "privacy", name: "Privacy" },
]);

const filteredAuditEvents = computed(() => {
  let events = auditEvents.value;

  // Apply search filter
  if (auditSearchQuery.value) {
    const query = auditSearchQuery.value.toLowerCase();
    events = events.filter(
      (event) =>
        event.action.toLowerCase().includes(query) ||
        JSON.stringify(event.details).toLowerCase().includes(query),
    );
  }

  // Apply category filter
  if (auditFilter.value !== "all") {
    events = events.filter((event) => {
      switch (auditFilter.value) {
        case "login":
          return (
            event.action.includes("login") || event.action.includes("logout")
          );
        case "content":
          return (
            event.action.includes("content") || event.action.includes("library")
          );
        case "security":
          return (
            event.action.includes("security") || event.action.includes("2fa")
          );
        case "admin":
          return (
            event.action.includes("admin") || event.action.includes("role")
          );
        default:
          return true;
      }
    });
  }

  return events;
});

// Methods
const refreshSecurityData = async () => {
  loading.value = true;
  try {
    await securityStore.fetchUserSessions();
    // Refresh other security data as needed
  } catch (error) {
    console.error("Error refreshing security data:", error);
  } finally {
    loading.value = false;
  }
};

const terminateSession = async (sessionId) => {
  try {
    await securityStore.terminateSession(sessionId);
  } catch (error) {
    console.error("Error terminating session:", error);
  }
};

const terminateAllOtherSessions = async () => {
  try {
    await securityStore.terminateAllOtherSessions();
  } catch (error) {
    console.error("Error terminating sessions:", error);
  }
};

const savePrivacySettings = async () => {
  try {
    await securityStore.updatePrivacySettings(privacySettings.value);
  } catch (error) {
    console.error("Error saving privacy settings:", error);
  }
};

const exportUserData = async () => {
  try {
    const data = await securityStore.exportUserData();

    // Create download
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `user-data-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Error exporting user data:", error);
  }
};

const deleteUserData = async () => {
  try {
    await securityStore.deleteUserData();
    showDeleteDataConfirm.value = false;
    // Redirect to login or home page
  } catch (error) {
    console.error("Error deleting user data:", error);
  }
};

const exportAuditLog = () => {
  const data = {
    timestamp: new Date().toISOString(),
    events: filteredAuditEvents.value,
    filters: {
      search: auditSearchQuery.value,
      category: auditFilter.value,
    },
  };

  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `audit-log-${new Date().toISOString().split("T")[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

const executeRecommendation = (recommendation) => {
  switch (recommendation.action) {
    case "enable2FA":
      activeTab.value = "security";
      // Navigate to 2FA settings
      break;
    case "reduceTimeout":
      // Open session timeout settings
      break;
    case "reviewSessions":
      activeTab.value = "sessions";
      break;
    case "reviewPrivacy":
      activeTab.value = "privacy";
      break;
  }
};

const showEventDetails = (event) => {
  // Show event details modal or navigate to detailed view
  console.log("Show event details:", event);
};

// Utility methods
const getRecommendationClass = (priority) => {
  switch (priority) {
    case "high":
      return "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20";
    case "medium":
      return "border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20";
    case "low":
      return "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20";
    default:
      return "border-gray-200 bg-gray-50 dark:border-gray-600 dark:bg-gray-700";
  }
};

const getRecommendationDotClass = (priority) => {
  switch (priority) {
    case "high":
      return "bg-red-500";
    case "medium":
      return "bg-yellow-500";
    case "low":
      return "bg-blue-500";
    default:
      return "bg-gray-500";
  }
};

const getEventSeverityColor = (severity) => {
  switch (severity) {
    case "critical":
      return "bg-red-500";
    case "high":
      return "bg-orange-500";
    case "warning":
      return "bg-yellow-500";
    case "info":
      return "bg-blue-500";
    default:
      return "bg-gray-500";
  }
};

const getActionClass = (action) => {
  if (action.includes("login") || action.includes("logout")) {
    return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
  }
  if (action.includes("security") || action.includes("2fa")) {
    return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
  }
  if (action.includes("admin") || action.includes("role")) {
    return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200";
  }
  return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
};

const getDeviceIcon = (deviceType) => {
  switch (deviceType) {
    case "mobile":
      return "📱";
    case "tablet":
      return "📱";
    case "desktop":
      return "💻";
    default:
      return "🖥️";
  }
};

const formatEventType = (type) => {
  return type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
};

const formatEventTime = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return "Just now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return date.toLocaleDateString();
};

const formatAuditTime = (timestamp) => {
  return new Date(timestamp).toLocaleString();
};

const formatActionName = (action) => {
  return action.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
};

const formatEventDetails = (details) => {
  if (!details || typeof details !== "object") return "N/A";

  const keys = Object.keys(details);
  if (keys.length === 0) return "N/A";

  if (keys.length === 1) {
    return `${keys[0]}: ${details[keys[0]]}`;
  }

  return `${keys.length} details`;
};

const formatLastActive = (timestamp) => {
  if (!timestamp) return "Unknown";

  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return "Active now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return `${Math.floor(diff / 86400000)}d ago`;
};

const formatSessionTime = (timestamp) => {
  return new Date(timestamp).toLocaleDateString();
};

// Lifecycle
onMounted(async () => {
  await refreshSecurityData();
});
</script>

<style scoped>
.security-dashboard {
  max-height: 90vh;
  overflow-y: auto;
}
</style>
