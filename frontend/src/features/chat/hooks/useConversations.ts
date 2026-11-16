import { useCallback } from 'react'

import { type AsyncData, useAsyncData } from '@/hooks/useAsyncData'
import { type ApiError, toApiError } from '@/services/api/errors'
import type { Page } from '@/types/api'

import { deleteConversation, listConversations, renameConversation } from '../api'
import type { ConversationSummary } from '../types'

export interface UseConversations {
  data: AsyncData<Page<ConversationSummary>>
  /** Resolves to the error to show, or null. */
  rename: (id: string, title: string) => Promise<ApiError | null>
  remove: (id: string) => Promise<ApiError | null>
}

/** The conversation list of the sidebar. Changes refresh it in the background. */
export function useConversations(): UseConversations {
  const data = useAsyncData(listConversations)
  const { refresh } = data

  const run = useCallback(
    async (change: () => Promise<unknown>) => {
      try {
        await change()
        refresh()
        return null
      } catch (error) {
        return toApiError(error)
      }
    },
    [refresh],
  )

  return {
    data,
    rename: (id, title) => run(() => renameConversation(id, title)),
    remove: (id) => run(() => deleteConversation(id)),
  }
}
