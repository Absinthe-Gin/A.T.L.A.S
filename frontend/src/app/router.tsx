import { createBrowserRouter, type RouteObject } from 'react-router'

import { ChatPage } from '@/pages/ChatPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { FinancePage } from '@/pages/FinancePage'
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
          { path: 'chat/:conversationId', element: <ChatPage /> },
          // Planned modules: replace each placeholder with the real page when implemented.
          { path: 'finance', element: <FinancePage /> },
          // Travel pages carry the map library: loaded only when opened.
          { path: 'travel', lazy: async () => ({ Component: (await import('@/pages/TravelPage')).TravelPage }) },
          {
            path: 'travel/:planId',
            lazy: async () => ({ Component: (await import('@/pages/TravelPlanPage')).TravelPlanPage }),
          },
          { path: 'food', lazy: async () => ({ Component: (await import('@/pages/FoodPage')).FoodPage }) },
          { path: 'memory', element: <ModulePlaceholderPage moduleId="memory" /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
]

export const router = createBrowserRouter(routes)
