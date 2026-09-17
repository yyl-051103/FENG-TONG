import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "../stores/user";

const routes = [
  {
    path: "/",
    name: "Home",
    component: () => import("../views/HomeView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/LoginView.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("../views/RegisterView.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/news/create",
    name: "Create",
    component: () => import("../views/CreateView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/news/:id",
    name: "Detail",
    component: () => import("../views/DetailView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/news/my",
    name: "MyNews",
    component: () => import("../views/MyNewsView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/profile",
    name: "Profile",
    component: () => import("../views/ProfileView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/admin",
    name: "Admin",
    component: () => import("../views/AdminView.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: "/admin/gifts",
    name: "AdminGifts",
    component: () => import("../views/admin/GiftManageView.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: "/search",
    name: "Search",
    component: () => import("../views/SearchView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/score",
    name: "Score",
    component: () => import("../views/ScoreView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/favorites",
    name: "Favorites",
    component: () => import("../views/FavoritesView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/gifts",
    name: "Gifts",
    component: () => import("../views/GiftListView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/gifts/:id",
    name: "GiftDetail",
    component: () => import("../views/GiftDetailView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/orders",
    name: "Orders",
    component: () => import("../views/OrderListView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/flash-sale",
    name: "FlashSale",
    component: () => import("../views/FlashSaleView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/checkout/:orderNo",
    name: "Checkout",
    component: () => import("../views/CheckoutView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/checkout/callback",
    name: "CheckoutCallback",
    component: () => import("../views/CheckoutCallbackView.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/admin/flash-sales",
    name: "AdminFlashSales",
    component: () => import("../views/admin/FlashSaleManageView.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: "/map",
    name: "Map",
    component: () => import("../views/MapView.vue"),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  const store = useUserStore();
  if (to.meta.requiresAuth && !store.isLoggedIn) {
    next(`/login?redirect=${encodeURIComponent(to.fullPath)}`);
  } else if (to.meta.requiresAdmin && !store.isAdmin) {
    next("/");
  } else {
    next();
  }
});

export default router;
