import type { AppProps } from "next/app";
import "../styles/globals.css";
import "maplibre-gl/dist/maplibre-gl.css";

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
