import { createApp } from "vue";
import { createPinia } from "pinia";
import router from "./router";
import App from "./App.vue";
import axios from "axios";
import "./style.css";

// Configure axios
axios.defaults.baseURL = "/api";

// Check for token in localStorage or sessionStorage
const token = localStorage.getItem("token") || sessionStorage.getItem("token");
if (token) {
  axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

// Create app
const app = createApp(App);

// Use plugins
app.use(createPinia());
app.use(router);

// Mount app
app.mount("#app");
