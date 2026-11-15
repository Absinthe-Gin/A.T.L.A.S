import { createBrowserRouter, type RouteObject } from 'react-router'

import { ChatPage } from '@/pages/ChatPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ModulePlaceholderPage } from '@/pages/ModulePlaceholderPage'
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
          { index: true, element: <DashboardPage /> },
          { path: 'chat', element: <ChatPage /> },
          // Planned modules: replace each placeholder with the real page when implemented.
          { path: 'finance', element: <ModulePlaceholderPage moduleId="finance" /> },
          { path: 'travel', element: <ModulePlaceholderPage moduleId="travel" /> },
          { path: 'food', element: <ModulePlaceholderPage moduleId="food" /> },
          { path: 'memory', element: <ModulePlaceholderPage moduleId="memory" /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
]

export const router = createBrowserRouter(routes)
