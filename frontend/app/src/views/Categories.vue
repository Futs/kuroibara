<template>
  <div class="categories">
    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
      <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            Categories
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Organize your manga collection
          </p>
        </div>
        <button
          @click="showAddCategoryModal = true"
          class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <svg class="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Category
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="px-4 py-12 flex justify-center">
        <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="px-4 py-5 sm:p-6">
        <div class="rounded-md bg-red-50 dark:bg-red-900 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-red-400 dark:text-red-300" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
                {{ error }}
              </h3>
              <div class="mt-2 text-sm text-red-700 dark:text-red-300">
                <button
                  @click="fetchCategories"
                  class="font-medium underline hover:text-red-600 dark:hover:text-red-400"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="categories.length === 0" class="px-4 py-12 text-center">
        <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No categories</h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Get started by creating a new category.
        </p>
        <div class="mt-6">
          <button
            @click="showAddCategoryModal = true"
            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg class="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add Category
          </button>
        </div>
      </div>

      <!-- Categories List -->
      <div v-else class="px-4 py-5 sm:p-6">
        <ul role="list" class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <li
            v-for="category in categories"
            :key="category.id"
            class="col-span-1 bg-white dark:bg-dark-700 rounded-lg shadow divide-y divide-gray-200 dark:divide-dark-600"
          >
            <div class="w-full flex items-center justify-between p-6 space-x-6">
              <div class="flex-1 truncate">
                <div class="flex items-center space-x-3">
                  <h3 class="text-gray-900 dark:text-white text-sm font-medium truncate">{{ category.name }}</h3>
                  <span v-if="category.is_default" class="flex-shrink-0 inline-block px-2 py-0.5 text-green-800 dark:text-green-200 text-xs font-medium bg-green-100 dark:bg-green-900 rounded-full">
                    Default
                  </span>
                </div>
                <p class="mt-1 text-gray-500 dark:text-gray-400 text-sm truncate">
                  {{ category.manga_count || 0 }} manga
                </p>
              </div>
              <div class="flex-shrink-0 h-10 w-10 bg-primary-500 rounded-full flex items-center justify-center">
                <svg class="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
            </div>
            <div>
              <div class="-mt-px flex divide-x divide-gray-200 dark:divide-dark-600">
                <div class="w-0 flex-1 flex">
                  <button
                    @click="viewCategory(category.id)"
                    class="relative -mr-px w-0 flex-1 inline-flex items-center justify-center py-4 text-sm text-gray-700 dark:text-gray-300 font-medium border border-transparent rounded-bl-lg hover:text-gray-500 dark:hover:text-white"
                  >
                    <svg class="w-5 h-5 text-gray-400 dark:text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    <span class="ml-3">View</span>
                  </button>
                </div>
                <div class="-ml-px w-0 flex-1 flex">
                  <button
                    @click="editCategory(category)"
                    class="relative w-0 flex-1 inline-flex items-center justify-center py-4 text-sm text-gray-700 dark:text-gray-300 font-medium border border-transparent hover:text-gray-500 dark:hover:text-white"
                  >
                    <svg class="w-5 h-5 text-gray-400 dark:text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    <span class="ml-3">Edit</span>
                  </button>
                </div>
                <div class="-ml-px w-0 flex-1 flex">
                  <button
                    @click="deleteCategory(category)"
                    :disabled="category.is_default"
                    class="relative w-0 flex-1 inline-flex items-center justify-center py-4 text-sm text-gray-700 dark:text-gray-300 font-medium border border-transparent rounded-br-lg hover:text-gray-500 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg class="w-5 h-5 text-gray-400 dark:text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    <span class="ml-3">Delete</span>
                  </button>
                </div>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- Add/Edit Category Modal -->
    <div v-if="showAddCategoryModal || showEditCategoryModal" class="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 dark:bg-dark-900 bg-opacity-75 dark:bg-opacity-75 transition-opacity" aria-hidden="true" @click="closeModal"></div>

        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        <div class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div>
            <div class="mt-3 text-center sm:mt-5">
              <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white" id="modal-title">
                {{ showEditCategoryModal ? 'Edit Category' : 'Add New Category' }}
              </h3>
              <div class="mt-2">
                <div class="space-y-4">
                  <div>
                    <label for="category-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 text-left">
                      Name
                    </label>
                    <div class="mt-1">
                      <input
                        type="text"
                        id="category-name"
                        v-model="categoryForm.name"
                        class="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                        placeholder="Category name"
                      />
                    </div>
                  </div>

                  <div>
                    <label for="category-description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 text-left">
                      Description (optional)
                    </label>
                    <div class="mt-1">
                      <textarea
                        id="category-description"
                        v-model="categoryForm.description"
                        rows="3"
                        class="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                        placeholder="Category description"
                      ></textarea>
                    </div>
                  </div>

                  <div class="flex items-start">
                    <div class="flex items-center h-5">
                      <input
                        id="category-default"
                        v-model="categoryForm.is_default"
                        type="checkbox"
                        class="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 dark:border-dark-600 rounded"
                      />
                    </div>
                    <div class="ml-3 text-sm">
                      <label for="category-default" class="font-medium text-gray-700 dark:text-gray-300">
                        Set as default category
                      </label>
                      <p class="text-gray-500 dark:text-gray-400">
                        New manga will be automatically added to this category
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
            <button
              type="button"
              @click="saveCategory"
              :disabled="!categoryForm.name || formSubmitting"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="formSubmitting" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ showEditCategoryModal ? 'Update' : 'Create' }}
            </button>
            <button
              type="button"
              @click="closeModal"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:col-start-1 sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 dark:bg-dark-900 bg-opacity-75 dark:bg-opacity-75 transition-opacity" aria-hidden="true" @click="showDeleteModal = false"></div>

        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        <div class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div class="sm:flex sm:items-start">
            <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900 sm:mx-0 sm:h-10 sm:w-10">
              <svg class="h-6 w-6 text-red-600 dark:text-red-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white" id="modal-title">
                Delete Category
              </h3>
              <div class="mt-2">
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Are you sure you want to delete the category "{{ selectedCategory?.name }}"? This action cannot be undone.
                </p>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              @click="confirmDeleteCategory"
              :disabled="deleteSubmitting"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="deleteSubmitting" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Delete
            </button>
            <button
              type="button"
              @click="showDeleteModal = false"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:w-auto sm:text-sm"
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
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

const categories = ref([]);
const loading = ref(true);
const error = ref(null);

const showAddCategoryModal = ref(false);
const showEditCategoryModal = ref(false);
const showDeleteModal = ref(false);
const formSubmitting = ref(false);
const deleteSubmitting = ref(false);
const selectedCategory = ref(null);

const categoryForm = ref({
  id: null,
  name: '',
  description: '',
  is_default: false,
});

const fetchCategories = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await axios.get('/v1/categories');
    categories.value = response.data;
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load categories';
    console.error('Error fetching categories:', err);
  } finally {
    loading.value = false;
  }
};

const viewCategory = (categoryId) => {
  router.push(`/library?category=${categoryId}`);
};

const editCategory = (category) => {
  selectedCategory.value = category;
  categoryForm.value = {
    id: category.id,
    name: category.name,
    description: category.description || '',
    is_default: category.is_default || false,
  };
  showEditCategoryModal.value = true;
};

const deleteCategory = (category) => {
  if (category.is_default) return;

  selectedCategory.value = category;
  showDeleteModal.value = true;
};

const saveCategory = async () => {
  if (!categoryForm.value.name) return;

  formSubmitting.value = true;

  try {
    if (showEditCategoryModal.value) {
      // Update existing category
      await axios.put(`/v1/categories/${categoryForm.value.id}`, categoryForm.value);
    } else {
      // Create new category
      await axios.post('/v1/categories', categoryForm.value);
    }

    // Refresh categories
    await fetchCategories();

    // Close modal
    closeModal();
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save category';
    console.error('Error saving category:', err);
  } finally {
    formSubmitting.value = false;
  }
};

const confirmDeleteCategory = async () => {
  if (!selectedCategory.value) return;

  deleteSubmitting.value = true;

  try {
    await axios.delete(`/v1/categories/${selectedCategory.value.id}`);

    // Refresh categories
    await fetchCategories();

    // Close modal
    showDeleteModal.value = false;
    selectedCategory.value = null;
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to delete category';
    console.error('Error deleting category:', err);
  } finally {
    deleteSubmitting.value = false;
  }
};

const closeModal = () => {
  showAddCategoryModal.value = false;
  showEditCategoryModal.value = false;

  // Reset form
  categoryForm.value = {
    id: null,
    name: '',
    description: '',
    is_default: false,
  };

  selectedCategory.value = null;
};

onMounted(() => {
  fetchCategories();
});
</script>
