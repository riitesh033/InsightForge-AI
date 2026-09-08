import axios from "axios";

/*
|--------------------------------------------------------------------------
| API Configuration
|--------------------------------------------------------------------------
*/

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||
    "http://localhost:8000/api/v1",

  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },

  timeout: 30000,
});


/*
|--------------------------------------------------------------------------
| Request Interceptor
|--------------------------------------------------------------------------
*/

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


/*
|--------------------------------------------------------------------------
| Response Interceptor
|--------------------------------------------------------------------------
*/

api.interceptors.response.use(
  (response) => {
    return response;
  },

  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");

      delete api.defaults.headers.common.Authorization;

      const currentPath = window.location.pathname;

      const authPages = [
        "/login",
        "/register",
        "/forgot-password",
      ];

      if (!authPages.includes(currentPath)) {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);


export default api;