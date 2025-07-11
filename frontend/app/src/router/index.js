import { createRouter, createWebHistory } from "vue-router";

// Layouts
import DefaultLayout from "../layouts/DefaultLayout.vue";

// Pages
import Home from "../views/Home.vue";
import Login from "../views/auth/Login.vue";
import Register from "../views/auth/Register.vue";
import Profile from "../views/auth/Profile.vue";
import Library from "../views/Library.vue";
import MangaDetails from "../views/MangaDetails.vue";
import MangaReader from "../views/MangaReader.vue";
import Search from "../views/Search.vue";
import Categories from "../views/Categories.vue";
import ReadingLists from "../views/ReadingLists.vue";
import Settings from "../views/Settings.vue";
import Recovery from "../views/Recovery.vue";
import Backup from "../views/Backup.vue";
import NotFound from "../views/NotFound.vue";

// Route Guards
const requireAuth = (to, from, next) => {
  const token =
    localStorage.getItem("token") || sessionStorage.getItem("token");
  if (token) {
    next();
  } else {
    next("/login");
  }
};

const routes = [
  {
    path: "/",
    component: DefaultLayout,
    children: [
      {
        path: "",
        name: "home",
        component: Home,
      },
      {
        path: "login",
        name: "login",
        component: Login,
      },
      {
        path: "register",
        name: "register",
        component: Register,
      },
      {
        path: "profile",
        name: "profile",
        component: Profile,
        beforeEnter: requireAuth,
      },
      {
        path: "library",
        name: "library",
        component: Library,
        beforeEnter: requireAuth,
      },
      {
        path: "manga/:id",
        name: "manga-details",
        component: MangaDetails,
      },
      {
        path: "manga/external/:provider/:id",
        name: "external-manga-details",
        component: MangaDetails,
      },
      {
        path: "read/:id/:chapter?/:page?",
        name: "manga-reader",
        component: MangaReader,
        beforeEnter: requireAuth,
      },
      {
        path: "search",
        name: "search",
        component: Search,
      },
      {
        path: "categories",
        name: "categories",
        component: Categories,
        beforeEnter: requireAuth,
      },
      {
        path: "reading-lists",
        name: "reading-lists",
        component: ReadingLists,
        beforeEnter: requireAuth,
      },
      {
        path: "settings",
        name: "settings",
        component: Settings,
        beforeEnter: requireAuth,
      },
      {
        path: "recovery",
        name: "recovery",
        component: Recovery,
        beforeEnter: requireAuth,
      },
      {
        path: "backup",
        name: "backup",
        component: Backup,
        beforeEnter: requireAuth,
      },
      {
        path: "/:pathMatch(.*)*",
        name: "not-found",
        component: NotFound,
      },
      {
        path: "/profile/edit",
        name: "EditProfilePicture",
        component: () => import("../views/auth/EditProfilePicture.vue"),
        meta: { requiresAuth: true },
      },
      {
        path: "/profile/accounts",
        name: "LinkAccounts",
        component: () => import("../views/auth/LinkAccounts.vue"),
        meta: { requiresAuth: true },
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
