import nextEnv from "@next/env";
import { fileURLToPath } from "node:url";

const projectRoot = fileURLToPath(new URL("../", import.meta.url));
nextEnv.loadEnvConfig(projectRoot, process.env.NODE_ENV === "development");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
