import path from "node:path";

import type { NextConfig } from "next";

const config: NextConfig = {
  ...(process.env.VERCEL
    ? {}
    : { output: "standalone", outputFileTracingRoot: path.join(__dirname, "../..") }),
};

export default config;
