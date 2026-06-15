import { Fragment, Suspense, lazy } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { CssBaseline } from "@mui/material";
import { ThemeProvider } from "@mui/material/styles";
import { QueryClientProvider } from "@tanstack/react-query";
import { routes } from "routes";
import { theme } from "theme";
import { queryClient } from "lib/queryClient";
import { useFirebase } from "hooks/useFirebase";
import ToastMessage from "components/toast-message";
import ReactGA from "react-ga4"; // import react-ga
import * as Sentry from "@sentry/react";

import reportWebVitals from "./reportWebVitals";
import Loader from "components/loader";
import ErrorBoundary from "components/error-boundary";

import "theme/styles.css";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import "@fontsource/lato";

import "locales/i18n";

if (import.meta.env.VITE_GA_MEASUREMENT_ID) {
  ReactGA.initialize(import.meta.env.VITE_GA_MEASUREMENT_ID);
}

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate: 0.2,
    environment: import.meta.env.MODE,
  });
}

const ReactQueryDevtools = import.meta.env.DEV
  ? lazy(() =>
    import("@tanstack/react-query-devtools").then((module) => ({
      default: module.ReactQueryDevtools,
    }))
  )
  : null;

const APP = () => {
  useFirebase();
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Suspense fallback={<Loader />}>
        <Routes>
          {routes.map((route, key) => (
            <Fragment key={key}>
              {/* Check if has no children */}
              {!route.children && (
                <Route
                  path={route.path}
                  exact={route.exact}
                  element={route.element}
                  key={key}
                />
              )}

              {/* Check if has children */}
              {route.children?.length > 0 && (
                <Route
                  path={route.path}
                  exact={route.exact}
                  element={route.element}
                  key={key}
                >
                  {route.children.map((route, key) => (
                    <Route
                      path={route.path}
                      exact={route.exact}
                      element={route.element}
                      key={key}
                    />
                  ))}
                </Route>
              )}
            </Fragment>
          ))}
        </Routes>
      </Suspense>
    </ThemeProvider>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <ErrorBoundary>
        <APP />
      </ErrorBoundary>
    </BrowserRouter>
    <ToastMessage />
    {ReactQueryDevtools && (
      <Suspense fallback={null}>
        <ReactQueryDevtools initialIsOpen={false} />
      </Suspense>
    )}
  </QueryClientProvider>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
