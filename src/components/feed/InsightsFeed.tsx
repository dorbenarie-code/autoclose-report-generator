import React, { useEffect, useState, Fragment } from 'react'
import { getInsights, createTaskFromInsight, type Insight } from '../../lib/api'
import { Loader } from '../ui/loader'
import { Dialog, Transition } from '@headlessui/react'
import {
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline'
import { format } from 'date-fns'

const severityConfig: Record<Insight['severity'], {
  container: string
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>
}> = {
  critical: {
    container: 'border-red-500 bg-red-50/30 text-red-800',
    icon: ExclamationCircleIcon,
  },
  warning: {
    container: 'border-yellow-400 bg-yellow-50/30 text-yellow-800',
    icon: ExclamationTriangleIcon,
  },
  info: {
    container: 'border-blue-400 bg-blue-50/30 text-blue-800',
    icon: InformationCircleIcon,
  },
}

export const InsightsFeed: React.FC<{ limit?: number }> = ({ limit = 5 }) => {
  const [insights, setInsights] = useState<Insight[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAll, setShowAll] = useState(false)
  const [selected, setSelected] = useState<Insight | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const data = await getInsights(50)
        setInsights(data)
      } catch {
        setError('Failed to load insights.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const displayList = showAll ? insights : insights.slice(0, limit)

  // Group by severity
  const grouped = displayList.reduce<Record<string, Insight[]>>((acc, item) => {
    acc[item.severity] = acc[item.severity] || []
    acc[item.severity].push(item)
    return acc
  }, {})

  if (loading) {
    // Skeleton placeholders
    return (
      <div className="space-y-3">
        {Array.from({ length: limit }).map((_, idx) => (
          <div
            key={idx}
            className="h-20 rounded border bg-gray-200 animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (error) {
    return <div className="text-red-600 p-2">{error}</div>
  }

  return (
    <div className="space-y-6">
      {(['critical', 'warning', 'info'] as Insight['severity'][]).map((sev) => (
        grouped[sev]?.length ? (
          <div key={sev}>
            <h3 className="text-lg font-semibold capitalize">
              {sev}
            </h3>
            <div className="mt-2 space-y-2">
              {grouped[sev].map((ins) => {
                const { container, icon: Icon } = severityConfig[ins.severity]
                return (
                  <div
                    key={ins.id}
                    onClick={() => setSelected(ins)}
                    className={
                      `p-3 rounded border cursor-pointer hover:shadow transition ${container}`
                    }
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="w-5 h-5" />
                      <span className="font-semibold">{ins.title}</span>
                      <span className="ml-auto text-xs text-gray-500">
                        {format(new Date(ins.createdAt), 'HH:mm:ss')}
                      </span>
                    </div>
                    <p className="text-sm mt-1 text-gray-700 line-clamp-2">
                      {ins.message}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        ) : null
      ))}

      {insights.length > limit && (
        <button
          onClick={() => setShowAll((prev) => !prev)}
          className="text-blue-500 text-sm hover:underline"
        >
          {showAll ? 'Show less' : 'Show more'}
        </button>
      )}

      {selected && (
        <Transition.Root show onClose={() => setSelected(null)} as={Fragment}>
          <Dialog
            onClose={() => setSelected(null)}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <Dialog.Overlay className="fixed inset-0 bg-black/30" />
            <Transition.Child
              as={Fragment}
              enter="transition ease-out duration-200"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="transition ease-in duration-150"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
                <div className="flex items-center gap-2 mb-4">
                  {React.createElement(
                    severityConfig[selected.severity].icon,
                    { className: 'w-6 h-6 text-current' }
                  )}
                  <Dialog.Title className="text-xl font-semibold">
                    {selected.title}
                  </Dialog.Title>
                </div>
                <div className="mb-4 space-y-2 text-gray-700">
                  <p>{selected.message}</p>
                  <p className="text-xs text-gray-500">
                    {format(new Date(selected.createdAt), 'PPpp')}
                  </p>
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setSelected(null)}
                    className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
                  >
                    Close
                  </button>
                  <button
                    onClick={async () => {
                      await createTaskFromInsight(selected.id)
                      setSelected(null)
                    }}
                    className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
                  >
                    Create Task
                  </button>
                </div>
              </div>
            </Transition.Child>
          </Dialog>
        </Transition.Root>
      )}
    </div>
  )
}
