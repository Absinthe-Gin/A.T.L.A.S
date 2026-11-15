import { useCallback, useState } from 'react'

import { type AsyncData, useAsyncData } from '@/hooks/useAsyncData'
import { type ApiError, toApiError } from '@/services/api/errors'
import type { Page } from '@/types/api'

import { addItem, createPlan, deleteItem, deletePlan, getPlan, listPlans, updatePlan } from '../api'
import type { ItemCreate, Plan, PlanCreate, PlanDetail, PlanUpdate } from '../types'

/** Outcome of a change: done (with the saved value), or the error to show next to the form. */
export type MutationResult<T = undefined> = { ok: true; value: T } | { ok: false; error: ApiError }

function useMutation(refresh: () => void) {
  const [saving, setSaving] = useState(false)
  const run = useCallback(
    async <T>(change: () => Promise<T>, { reload = true } = {}): Promise<MutationResult<T>> => {
      setSaving(true)
      try {
        const value = await change()
        if (reload) refresh()
        return { ok: true, value }
      } catch (error) {
        return { ok: false, error: toApiError(error) }
      } finally {
        setSaving(false)
      }
    },
    [refresh],
  )
  return { saving, run }
}

export interface UseTravelPlans {
  data: AsyncData<Page<Plan>>
  saving: boolean
  create: (data: PlanCreate) => Promise<MutationResult<PlanDetail>>
}

export function useTravelPlans(): UseTravelPlans {
  const data = useAsyncData(listPlans)
  const { saving, run } = useMutation(data.refresh)
  return { data, saving, create: (input) => run(() => createPlan(input)) }
}

export interface UsePlan {
  data: AsyncData<PlanDetail>
  saving: boolean
  update: (data: PlanUpdate) => Promise<MutationResult<PlanDetail>>
  remove: () => Promise<MutationResult<void>>
  addItem: (data: ItemCreate) => Promise<MutationResult<unknown>>
  removeItem: (itemId: string) => Promise<MutationResult<void>>
}

/** One plan with its itinerary. After a change the plan is fetched again in the background. */
export function usePlan(planId: string): UsePlan {
  const fetcher = useCallback((signal: AbortSignal) => getPlan(planId, signal), [planId])
  const data = useAsyncData(fetcher)
  const { saving, run } = useMutation(data.refresh)
  return {
    data,
    saving,
    update: (input) => run(() => updatePlan(planId, input)),
    // A deleted plan cannot be fetched again; the page navigates away instead.
    remove: () => run(() => deletePlan(planId), { reload: false }),
    addItem: (input) => run(() => addItem(planId, input)),
    removeItem: (itemId) => run(() => deleteItem(planId, itemId)),
  }
}
