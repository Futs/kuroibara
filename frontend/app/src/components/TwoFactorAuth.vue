<template>
  <div
    class="two-factor-auth bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6"
  >
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
        Two-Factor Authentication
      </h2>
      <div class="flex items-center space-x-2">
        <div
          class="w-3 h-3 rounded-full"
          :class="twoFactorEnabled ? 'bg-green-500' : 'bg-red-500'"
        ></div>
        <span class="text-sm text-gray-600 dark:text-gray-400">
          {{ twoFactorEnabled ? "Enabled" : "Disabled" }}
        </span>
      </div>
    </div>

    <!-- 2FA Status Overview -->
    <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg mb-6">
      <div class="flex items-start space-x-4">
        <div class="text-4xl">{{ twoFactorEnabled ? "🔒" : "🔓" }}</div>
        <div class="flex-1">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {{
              twoFactorEnabled
                ? "Two-Factor Authentication is Active"
                : "Secure Your Account"
            }}
          </h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            {{
              twoFactorEnabled
                ? "Your account is protected with two-factor authentication. You can manage your settings below."
                : "Add an extra layer of security to your account by enabling two-factor authentication."
            }}
          </p>

          <div v-if="!twoFactorEnabled" class="space-y-2">
            <div
              class="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400"
            >
              <svg
                class="w-4 h-4 text-green-500"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
              <span>Protects against unauthorized access</span>
            </div>
            <div
              class="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400"
            >
              <svg
                class="w-4 h-4 text-green-500"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
              <span>Works even if your password is compromised</span>
            </div>
            <div
              class="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400"
            >
              <svg
                class="w-4 h-4 text-green-500"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
              <span>Multiple authentication methods available</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Enable 2FA Section -->
    <div v-if="!twoFactorEnabled" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- TOTP Method -->
        <div
          class="border border-gray-200 dark:border-dark-600 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="text-center">
            <div class="text-4xl mb-3">📱</div>
            <h3
              class="text-lg font-semibold text-gray-900 dark:text-white mb-2"
            >
              Authenticator App
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Use apps like Google Authenticator, Authy, or 1Password to
              generate time-based codes.
            </p>
            <button
              @click="startTOTPSetup"
              :disabled="loading"
              class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {{ loading ? "Setting up..." : "Set Up" }}
            </button>
          </div>
        </div>

        <!-- SMS Method -->
        <div
          class="border border-gray-200 dark:border-dark-600 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="text-center">
            <div class="text-4xl mb-3">💬</div>
            <h3
              class="text-lg font-semibold text-gray-900 dark:text-white mb-2"
            >
              SMS Verification
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Receive verification codes via text message to your mobile phone.
            </p>
            <button
              @click="startSMSSetup"
              :disabled="loading"
              class="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {{ loading ? "Setting up..." : "Set Up" }}
            </button>
          </div>
        </div>

        <!-- Email Method -->
        <div
          class="border border-gray-200 dark:border-dark-600 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="text-center">
            <div class="text-4xl mb-3">📧</div>
            <h3
              class="text-lg font-semibold text-gray-900 dark:text-white mb-2"
            >
              Email Verification
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Receive verification codes via email to your registered email
              address.
            </p>
            <button
              @click="startEmailSetup"
              :disabled="loading"
              class="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {{ loading ? "Setting up..." : "Set Up" }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Manage 2FA Section -->
    <div v-else class="space-y-6">
      <!-- Current Methods -->
      <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Active Methods
        </h3>

        <div class="space-y-3">
          <div
            v-for="method in activeMethods"
            :key="method.id"
            class="flex items-center justify-between p-3 bg-white dark:bg-dark-800 rounded border"
          >
            <div class="flex items-center space-x-3">
              <div class="text-2xl">{{ getMethodIcon(method.type) }}</div>
              <div>
                <div class="font-medium text-gray-900 dark:text-white">
                  {{ getMethodName(method.type) }}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">
                  {{ getMethodDescription(method) }}
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span
                class="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded"
              >
                Active
              </span>
              <button
                @click="removeMethod(method)"
                class="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Backup Codes -->
      <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Backup Codes
          </h3>
          <button
            @click="generateBackupCodes"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Generate New Codes
          </button>
        </div>

        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Backup codes can be used to access your account if you lose access to
          your primary 2FA method. Each code can only be used once.
        </p>

        <div
          v-if="backupCodes.length > 0"
          class="grid grid-cols-2 md:grid-cols-4 gap-2"
        >
          <div
            v-for="(code, index) in backupCodes"
            :key="index"
            class="p-2 bg-white dark:bg-dark-800 rounded border text-center font-mono text-sm"
            :class="{ 'opacity-50 line-through': code.used }"
          >
            {{ code.code }}
          </div>
        </div>

        <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
          No backup codes generated yet
        </div>
      </div>

      <!-- Disable 2FA -->
      <div
        class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-6 rounded-lg"
      >
        <h3 class="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
          Disable Two-Factor Authentication
        </h3>
        <p class="text-sm text-red-700 dark:text-red-300 mb-4">
          Disabling 2FA will make your account less secure. You'll only need
          your password to sign in.
        </p>
        <button
          @click="showDisableConfirm = true"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Disable 2FA
        </button>
      </div>
    </div>

    <!-- TOTP Setup Modal -->
    <div
      v-if="showTOTPSetup"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showTOTPSetup = false"
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
          <div>
            <h3
              class="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4"
            >
              Set Up Authenticator App
            </h3>

            <div class="space-y-4">
              <div class="text-center">
                <div class="mb-4">
                  <img :src="qrCodeUrl" alt="QR Code" class="mx-auto" />
                </div>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Scan this QR code with your authenticator app
                </p>
                <div
                  class="bg-gray-100 dark:bg-dark-700 p-3 rounded font-mono text-sm break-all"
                >
                  {{ totpSecret }}
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  Or enter this secret manually
                </p>
              </div>

              <div>
                <label
                  class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Enter verification code from your app
                </label>
                <input
                  v-model="verificationCode"
                  type="text"
                  placeholder="000000"
                  maxlength="6"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white text-center font-mono text-lg"
                />
              </div>
            </div>
          </div>

          <div class="mt-5 sm:mt-6 flex space-x-3">
            <button
              @click="completeTOTPSetup"
              :disabled="!verificationCode || verificationCode.length !== 6"
              class="flex-1 inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 sm:text-sm"
            >
              Enable 2FA
            </button>
            <button
              @click="showTOTPSetup = false"
              class="flex-1 inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-700 text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Disable 2FA Confirmation Modal -->
    <div
      v-if="showDisableConfirm"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showDisableConfirm = false"
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
                Disable Two-Factor Authentication
              </h3>
              <div class="mt-2">
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Are you sure you want to disable two-factor authentication?
                  This will make your account less secure.
                </p>
                <div class="mt-4">
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                  >
                    Enter verification code to confirm
                  </label>
                  <input
                    v-model="disableVerificationCode"
                    type="text"
                    placeholder="000000"
                    maxlength="6"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white text-center font-mono"
                  />
                </div>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              @click="disableTwoFactor"
              :disabled="
                !disableVerificationCode || disableVerificationCode.length !== 6
              "
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Disable 2FA
            </button>
            <button
              @click="showDisableConfirm = false"
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

const securityStore = useSecurityStore();

// Local state
const loading = ref(false);
const showTOTPSetup = ref(false);
const showDisableConfirm = ref(false);
const verificationCode = ref("");
const disableVerificationCode = ref("");
const totpSecret = ref("");
const qrCodeUrl = ref("");

// Mock data for demonstration
const activeMethods = ref([
  {
    id: 1,
    type: "totp",
    name: "Google Authenticator",
    lastUsed: new Date(Date.now() - 3600000),
  },
]);

const backupCodes = ref([
  { code: "ABC123", used: false },
  { code: "DEF456", used: false },
  { code: "GHI789", used: true },
  { code: "JKL012", used: false },
  { code: "MNO345", used: false },
  { code: "PQR678", used: false },
  { code: "STU901", used: false },
  { code: "VWX234", used: false },
]);

// Computed properties
const twoFactorEnabled = computed(() => securityStore.twoFactorEnabled);

// Methods
const startTOTPSetup = async () => {
  loading.value = true;
  try {
    const result = await securityStore.enableTwoFactor("totp");
    totpSecret.value = result.secret;
    qrCodeUrl.value = result.qrCode;
    showTOTPSetup.value = true;
  } catch (error) {
    console.error("Error starting TOTP setup:", error);
  } finally {
    loading.value = false;
  }
};

const completeTOTPSetup = async () => {
  try {
    const isValid = await securityStore.verifyTwoFactor(verificationCode.value);
    if (isValid) {
      showTOTPSetup.value = false;
      verificationCode.value = "";
      // Refresh component state
    } else {
      alert("Invalid verification code. Please try again.");
    }
  } catch (error) {
    console.error("Error completing TOTP setup:", error);
  }
};

const startSMSSetup = async () => {
  loading.value = true;
  try {
    // Implement SMS setup
    console.log("Starting SMS setup...");
  } catch (error) {
    console.error("Error starting SMS setup:", error);
  } finally {
    loading.value = false;
  }
};

const startEmailSetup = async () => {
  loading.value = true;
  try {
    // Implement email setup
    console.log("Starting email setup...");
  } catch (error) {
    console.error("Error starting email setup:", error);
  } finally {
    loading.value = false;
  }
};

const disableTwoFactor = async () => {
  try {
    await securityStore.disableTwoFactor(disableVerificationCode.value);
    showDisableConfirm.value = false;
    disableVerificationCode.value = "";
  } catch (error) {
    console.error("Error disabling 2FA:", error);
    alert("Invalid verification code. Please try again.");
  }
};

const removeMethod = async (method) => {
  if (
    confirm(`Are you sure you want to remove ${getMethodName(method.type)}?`)
  ) {
    try {
      // Implement method removal
      activeMethods.value = activeMethods.value.filter(
        (m) => m.id !== method.id,
      );
    } catch (error) {
      console.error("Error removing method:", error);
    }
  }
};

const generateBackupCodes = async () => {
  try {
    // Generate new backup codes
    const newCodes = [
      "ABC123",
      "DEF456",
      "GHI789",
      "JKL012",
      "MNO345",
      "PQR678",
      "STU901",
      "VWX234",
    ].map((code) => ({ code, used: false }));

    backupCodes.value = newCodes;
  } catch (error) {
    console.error("Error generating backup codes:", error);
  }
};

// Utility methods
const getMethodIcon = (type) => {
  switch (type) {
    case "totp":
      return "📱";
    case "sms":
      return "💬";
    case "email":
      return "📧";
    default:
      return "🔐";
  }
};

const getMethodName = (type) => {
  switch (type) {
    case "totp":
      return "Authenticator App";
    case "sms":
      return "SMS Verification";
    case "email":
      return "Email Verification";
    default:
      return "Unknown Method";
  }
};

const getMethodDescription = (method) => {
  switch (method.type) {
    case "totp":
      return `Last used ${formatLastUsed(method.lastUsed)}`;
    case "sms":
      return `Phone: ***-***-${method.phone?.slice(-4) || "****"}`;
    case "email":
      return `Email: ${method.email?.replace(/(.{2})(.*)(@.*)/, "$1***$3") || "***@***.***"}`;
    default:
      return "No description available";
  }
};

const formatLastUsed = (timestamp) => {
  if (!timestamp) return "never";

  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return "just now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return `${Math.floor(diff / 86400000)}d ago`;
};

// Lifecycle
onMounted(() => {
  // Initialize component
});
</script>

<style scoped>
.two-factor-auth {
  max-height: 90vh;
  overflow-y: auto;
}
</style>
