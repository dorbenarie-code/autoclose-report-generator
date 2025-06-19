import React, { Fragment, useEffect, useRef } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import {
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'
import type { Insight } from '../../lib/api'

export interface InsightModalProps {
  insight: Insight
  onClose: () => void
  onCreateTask: (insight: Insight) => void
}

const severityConfig: Record<Insight['severity'], {
  label: string
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>
  container: string
}> = {
  critical: {
    label: 'Critical',
    icon: ExclamationCircleIcon,
    container: 'border-red-500 bg-red-50 text-red-800',
  },
  warning: {
    label: 'Warning',
    icon: ExclamationTriangleIcon,
    container: 'border-yellow-400 bg-yellow-50 text-yellow-800',
  },
  info: {
    label: 'Info',
    icon: InformationCircleIcon,
    container: 'border-blue-400 bg-blue-50 text-blue-800',
  },
}

export const InsightModal: React.FC<InsightModalProps> = ({ insight, onClose, onCreateTask }) => {
  const cancelButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    cancelButtonRef.current?.focus()
  }, [])

  const { icon: SeverityIcon, container } = severityConfig[insight.severity]

  return (
    <Transition.Root show as={Fragment}>
      <Dialog
        onClose={onClose}
        initialFocus={cancelButtonRef}
        className="fixed inset-0 z-50 overflow-y-auto"
      >
        <div className="flex min-h-screen items-center justify-center p-4 text-center">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-200"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-150"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Dialog.Overlay className="fixed inset-0 bg-black bg-opacity-30" />
          </Transition.Child>

          {/* This element is to trick the browser into centering the modal contents. */}
          <span className="inline-block h-screen align-middle" aria-hidden="true">
            &#8203;
          </span>

          <Transition.Child
            as={Fragment}
            enter="ease-out duration-200"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-150"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <div className="inline-block w-full max-w-lg transform overflow-hidden rounded-2xl border shadow-xl bg-white p-6 align-middle">
              <div className={`px-3 py-1 mb-4 inline-flex items-center space-x-2 rounded ${container} border`}>              
                <SeverityIcon className="w-5 h-5" />
                <span className="text-sm font-semibold">{severityConfig[insight.severity].label}</span>
              </div>
              <Dialog.Title as="h3" className="text-lg font-bold leading-6 text-gray-900">
                {insight.title}
              </Dialog.Title>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(insight.createdAt).toLocaleString()}
              </p>
              <div className="mt-4 text-gray-700 whitespace-pre-line">
                {insight.message}
              </div>

              {/* Meta section if exists */}
              {insight.meta && Object.keys(insight.meta).length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-600">Details</h4>
                  <ul className="mt-2 space-y-1 text-sm text-gray-700">
                    {Object.entries(insight.meta).map(([key, value]) => (
                      <li key={key} className="flex justify-between">
                        <span className="font-medium capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                        <span>{String(value)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  ref={cancelButtonRef}
                  className="px-4 py-2 rounded bg-gray-200 text-gray-700 hover:bg-gray-300 focus:outline-none"
                  onClick={onClose}
                >
                  Close
                </button>
                <button
                  type="button"
                  className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 focus:outline-none"
                  onClick={() => onCreateTask(insight)}
                >
                  Create Task
                </button>
              </div>
            </div>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  )
}
