import axios from "axios";

const api = axios.create({
  baseURL: "",
  withCredentials: true, // so SSR cookies also work if used
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function login(username, password) {
  const form = new FormData();
  form.append("username", username);
  form.append("password", password);
  const { data } = await api.post("/api/auth/token", form);
  localStorage.setItem("token", data.access_token);
  return data;
}

export async function register(payload) {
  const { data } = await api.post("/api/auth/register", payload);
  return data;
}

export async function me() {
  const { data } = await api.get("/api/auth/me");
  return data;
}

export async function feed() {
  const { data } = await api.get("/api/posts/feed/me");
  return data;
}

export async function createPost({ caption, file }) {
  const form = new FormData();
  form.append("caption", caption || "");
  if (file) form.append("image", file);
  const { data } = await api.post("/api/posts", form);
  return data;
}

export async function like(postId) {
  await api.post(`/api/likes/post/${postId}`);
}
export async function unlike(postId) {
  await api.post(`/api/likes/post/${postId}/unlike`);
}

export async function userProfile(username) {
  const { data } = await api.get(`/api/users/${username}`);
  return data;
}
export function avatarUrl(username) {
  return `https://api.dicebear.com/8.x/thumbs/svg?seed=${encodeURIComponent(username)}`;
}
