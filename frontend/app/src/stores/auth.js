import { defineStore } from 'pinia';
import axios from 'axios';
import router from '../router';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    getUser: (state) => state.user,
  },
  
  actions: {
    async login(email, password) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post('/api/v1/auth/login', {
          email,
          password,
        });
        
        const { access_token, user } = response.data;
        
        this.token = access_token;
        this.user = user;
        
        localStorage.setItem('token', access_token);
        
        // Set the Authorization header for all future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        router.push('/library');
      } catch (error) {
        this.error = error.response?.data?.detail || 'Login failed';
        console.error('Login error:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async register(email, username, password) {
      this.loading = true;
      this.error = null;
      
      try {
        await axios.post('/api/v1/auth/register', {
          email,
          username,
          password,
        });
        
        router.push('/login');
      } catch (error) {
        this.error = error.response?.data?.detail || 'Registration failed';
        console.error('Registration error:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchUser() {
      if (!this.token) return;
      
      this.loading = true;
      
      try {
        const response = await axios.get('/api/v1/users/me');
        this.user = response.data;
      } catch (error) {
        console.error('Error fetching user:', error);
        if (error.response?.status === 401) {
          this.logout();
        }
      } finally {
        this.loading = false;
      }
    },
    
    logout() {
      this.user = null;
      this.token = null;
      
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      
      router.push('/login');
    },
    
    initAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
        this.fetchUser();
      }
    },
  },
});
