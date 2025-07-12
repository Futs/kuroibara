<template>
  <div class="profile">
    <div class="bg-white dark:bg-dark-800 shadow overflow-hidden sm:rounded-lg">
      <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
        <div>
          <h3
            class="text-lg leading-6 font-medium text-gray-900 dark:text-white"
          >
            User Profile
          </h3>
          <p class="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
            Personal details and account settings
          </p>
        </div>
        <button
          @click="editMode = !editMode"
          class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-primary-700 dark:text-primary-300 bg-primary-100 dark:bg-primary-900 hover:bg-primary-200 dark:hover:bg-primary-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <svg
            v-if="!editMode"
            class="-ml-0.5 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
            />
          </svg>
          <svg
            v-else
            class="-ml-0.5 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
          {{ editMode ? "Cancel" : "Edit Profile" }}
        </button>
      </div>

      <div v-if="loading" class="px-4 py-5 sm:p-6 flex justify-center">
        <svg
          class="animate-spin h-8 w-8 text-primary-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      </div>

      <div v-else-if="error" class="px-4 py-5 sm:p-6">
        <div class="rounded-md bg-red-50 dark:bg-red-900 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg
                class="h-5 w-5 text-red-400 dark:text-red-300"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
                {{ error }}
              </h3>
            </div>
          </div>
        </div>
      </div>

      <div v-else>
        <form
          v-if="editMode"
          @submit.prevent="updateProfile"
          class="border-t border-gray-200 dark:border-dark-600"
        >
          <dl>
            <div
              class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Username
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <input
                  v-model="formData.username"
                  type="text"
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                />
              </dd>
            </div>
            <div
              class="bg-white dark:bg-dark-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Email address
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <input
                  v-model="formData.email"
                  type="email"
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                />
              </dd>
            </div>
            <div
              class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Full Name
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <input
                  v-model="formData.full_name"
                  type="text"
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                  placeholder="Your full name"
                />
              </dd>
            </div>
            <div
              class="bg-white dark:bg-dark-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Bio
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <textarea
                  v-model="formData.bio"
                  rows="3"
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                  placeholder="Tell us about yourself..."
                />
              </dd>
            </div>
            <div
              class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Avatar URL
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <input
                  v-model="formData.avatar"
                  type="url"
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                  placeholder="https://example.com/avatar.jpg"
                />
              </dd>
            </div>
            <div
              class="bg-white dark:bg-dark-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                AniList Username
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <input
                  v-model="formData.anilist_username"
                  type="text"
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                  placeholder="Your AniList username"
                />
              </dd>
            </div>
            <div
              class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                MyAnimeList Username
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <input
                  v-model="formData.myanimelist_username"
                  type="text"
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                  placeholder="Your MyAnimeList username"
                />
              </dd>
            </div>
            <div
              class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                New Password
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <input
                  v-model="formData.password"
                  type="password"
                  placeholder="Enter new password (leave blank to keep current)"
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                />
              </dd>
            </div>
            <div
              class="bg-white dark:bg-dark-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Confirm New Password
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <input
                  v-model="formData.confirmPassword"
                  type="password"
                  placeholder="Confirm new password (only if changing password)"
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                />
                <p
                  v-if="passwordMismatch"
                  class="mt-2 text-sm text-red-600 dark:text-red-400"
                >
                  Passwords do not match
                </p>
                <p
                  v-if="formData.password && !formData.confirmPassword"
                  class="mt-2 text-sm text-gray-500 dark:text-gray-400"
                >
                  Confirm password to change it, or leave both fields blank to keep current password.
                </p>
              </dd>
            </div>
            <div
              class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
            >
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Current Password
              </dt>
              <dd
                class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
              >
                <input
                  v-model="formData.currentPassword"
                  type="password"
                  placeholder="Required to save changes"
                  required
                  class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
                />
              </dd>
            </div>
          </dl>

          <div class="px-4 py-3 bg-gray-50 dark:bg-dark-700 text-right sm:px-6">
            <button
              type="button"
              @click="editMode = false"
              class="inline-flex justify-center py-2 px-4 border border-gray-300 dark:border-dark-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 mr-3"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="updateLoading || !canSubmit"
              class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
                v-if="updateLoading"
                class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                ></circle>
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Save
            </button>
          </div>
        </form>

        <dl v-else class="border-t border-gray-200 dark:border-dark-600">
          <div
            class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
          >
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              Username
            </dt>
            <dd
              class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
            >
              {{ user?.username }}
            </dd>
          </div>
          <div
            class="bg-white dark:bg-dark-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
          >
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              Email address
            </dt>
            <dd
              class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
            >
              {{ user?.email }}
            </dd>
          </div>
          <div
            class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
          >
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              Full Name
            </dt>
            <dd
              class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
            >
              {{ user?.full_name || "Not set" }}
            </dd>
          </div>
          <div
            class="bg-white dark:bg-dark-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
          >
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              Bio
            </dt>
            <dd
              class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
            >
              {{ user?.bio || "No bio provided" }}
            </dd>
          </div>
          <div
            class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
          >
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              Avatar
            </dt>
            <dd
              class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
            >
              <div v-if="user?.avatar" class="flex items-center space-x-3">
                <img
                  :src="user.avatar"
                  alt="Avatar"
                  class="h-10 w-10 rounded-full object-cover"
                />
                <span class="text-sm text-gray-500 dark:text-gray-400">{{
                  user.avatar
                }}</span>
              </div>
              <span v-else class="text-gray-500 dark:text-gray-400"
                >No avatar set</span
              >
            </dd>
          </div>
          <div
            class="bg-white dark:bg-dark-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
          >
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              AniList Account
            </dt>
            <dd
              class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
            >
              <a
                v-if="user?.anilist_username"
                :href="`https://anilist.co/user/${user.anilist_username}`"
                target="_blank"
                class="text-primary-600 dark:text-primary-400 hover:text-primary-500 dark:hover:text-primary-300"
              >
                {{ user.anilist_username }}
                <svg
                  class="inline h-4 w-4 ml-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  ></path>
                </svg>
              </a>
              <span v-else class="text-gray-500 dark:text-gray-400"
                >Not linked</span
              >
            </dd>
          </div>
          <div
            class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
          >
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              MyAnimeList Account
            </dt>
            <dd
              class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
            >
              <a
                v-if="user?.myanimelist_username"
                :href="`https://myanimelist.net/profile/${user.myanimelist_username}`"
                target="_blank"
                class="text-primary-600 dark:text-primary-400 hover:text-primary-500 dark:hover:text-primary-300"
              >
                {{ user.myanimelist_username }}
                <svg
                  class="inline h-4 w-4 ml-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  ></path>
                </svg>
              </a>
              <span v-else class="text-gray-500 dark:text-gray-400"
                >Not linked</span
              >
            </dd>
          </div>
          <div
            class="bg-gray-50 dark:bg-dark-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
          >
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              Account created
            </dt>
            <dd
              class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
            >
              {{ formatDate(user?.created_at) }}
            </dd>
          </div>
          <div
            class="bg-white dark:bg-dark-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6"
          >
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              Last login
            </dt>
            <dd
              class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2"
            >
              {{ formatDate(user?.last_login) }}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "../../stores/auth";
import api from "../../services/api.js";

const authStore = useAuthStore();

const loading = computed(() => authStore.loading);
const error = computed(() => authStore.error);
const user = computed(() => authStore.getUser);

const editMode = ref(false);
const updateLoading = ref(false);
const updateError = ref(null);

const formData = ref({
  username: "",
  email: "",
  full_name: "",
  bio: "",
  avatar: "",
  anilist_username: "",
  myanimelist_username: "",
  password: "",
  confirmPassword: "",
  currentPassword: "",
});

const passwordMismatch = computed(() => {
  // Only check password mismatch if both fields have content
  if (formData.value.password && formData.value.confirmPassword) {
    return formData.value.password !== formData.value.confirmPassword;
  }
  return false;
});

const isChangingPassword = computed(() => {
  // Consider it a password change if they have both password and confirmation
  return formData.value.password && formData.value.confirmPassword;
});

const hasPasswordError = computed(() => {
  // Show error if they're trying to change password but passwords don't match
  return isChangingPassword.value && passwordMismatch.value;
});

const canSubmit = computed(() => {
  // Always require current password
  if (!formData.value.currentPassword) {
    return false;
  }

  // Can't submit if there's a password mismatch error
  if (hasPasswordError.value) {
    return false;
  }

  // Can always submit for profile updates - password change is optional
  return true;
});

onMounted(() => {
  if (!user.value) {
    authStore.fetchUser();
  } else {
    resetForm();
  }
});

const resetForm = () => {
  if (user.value) {
    formData.value = {
      username: user.value.username,
      email: user.value.email,
      full_name: user.value.full_name || "",
      bio: user.value.bio || "",
      avatar: user.value.avatar || "",
      anilist_username: user.value.anilist_username || "",
      myanimelist_username: user.value.myanimelist_username || "",
      password: "",
      confirmPassword: "",
      currentPassword: "",
    };
  }
};

const updateProfile = async () => {
  if (!canSubmit.value) return;

  updateLoading.value = true;
  updateError.value = null;

  try {
    const payload = {
      username: formData.value.username,
      email: formData.value.email,
      full_name: formData.value.full_name,
      bio: formData.value.bio,
      avatar: formData.value.avatar,
      anilist_username: formData.value.anilist_username,
      myanimelist_username: formData.value.myanimelist_username,
      current_password: formData.value.currentPassword,
    };

    // Only include password if user is actually changing it (both fields filled)
    if (isChangingPassword.value) {
      payload.password = formData.value.password;
    }

    await api.put("/v1/users/me", payload);

    // Refresh user data
    await authStore.fetchUser();

    // Exit edit mode
    editMode.value = false;
  } catch (error) {
    updateError.value =
      error.response?.data?.detail || "Failed to update profile";
    console.error("Profile update error:", error);
  } finally {
    updateLoading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return "N/A";

  const date = new Date(dateString);
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};
</script>
