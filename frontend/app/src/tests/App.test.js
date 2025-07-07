import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import App from '../App.vue'

// Create a mock router for tests
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } }
  ]
})

describe('App.vue', () => {
  it('renders properly', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router],
        stubs: {
          'router-view': true
        }
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should have the correct structure', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router],
        stubs: {
          'router-view': true
        }
      }
    })

    // App.vue template only contains <router-view />, so check for that
    expect(wrapper.find('router-view-stub').exists()).toBe(true)
  })
})
