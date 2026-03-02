import Constants from "expo-constants";

export const API_BASE_URL =
  (Constants.expoConfig?.extra?.apiUrl as string) ??
  process.env.EXPO_PUBLIC_API_URL ??
  "http://localhost:8000/api/v1";
