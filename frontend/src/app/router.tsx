import { createBrowserRouter, type RouteObject } from 'react-router'

import { HomePage } from '@/pages/HomePage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { RouteErrorPage } from '@/pages/RouteErrorPage'

import { AppLayout } from './layouts/AppLayout'

/** Exported separately so tests can mount the same routes in a memory router. */
export const routes: RouteObject[] = [
  {
    element: <AppLayout />,
    children: [
      {
        // A failing page is replaced by the error page inside the layout.
        errorElement: <RouteErrorPage />,
        children: [
          { index: true, element: <HomePage /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
]

export const router = createBrowserRouter(routes)
