'use client';

import { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: T) => React.ReactNode;
  className?: string;
  headerClassName?: string;
  getValue?: (row: T) => any;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  initialSort?: { key: string; direction: 'asc' | 'desc' };
  onRowClick?: (row: T) => void;
  selectedRowKey?: string;
  getRowKey: (row: T, index: number) => string;
  className?: string;
  maxHeight?: string;
}

export default function DataTable<T>({
  data,
  columns,
  initialSort,
  onRowClick,
  selectedRowKey,
  getRowKey,
  className = '',
  maxHeight,
}: DataTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(initialSort || null);

  const sortedData = useMemo(() => {
    if (!sortConfig) return data;

    const column = columns.find(col => col.key === sortConfig.key);
    if (!column) return data;

    return [...data].sort((a, b) => {
      const aVal = column.getValue ? column.getValue(a) : (a as any)[sortConfig.key];
      const bVal = column.getValue ? column.getValue(b) : (b as any)[sortConfig.key];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const order = sortConfig.direction === 'asc' ? 1 : -1;
      return aVal < bVal ? -1 * order : 1 * order;
    });
  }, [data, sortConfig, columns]);

  const requestSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortIcon = (key: string) => {
    if (!sortConfig || sortConfig.key !== key) return <ChevronsUpDown size={12} className="text-ink-light opacity-30" />;
    return sortConfig.direction === 'asc' 
      ? <ChevronUp size={12} className="text-sage" /> 
      : <ChevronDown size={12} className="text-sage" />;
  };

  return (
    <div className={`border border-faint bg-white overflow-hidden flex flex-col ${className}`}>
      <div className="overflow-x-auto overflow-y-auto" style={{ maxHeight }}>
        <table className="w-full text-left text-sm whitespace-nowrap border-collapse">
          <thead className="bg-paper sticky top-0 z-10 border-b border-faint shadow-sm">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 font-semibold uppercase tracking-widest text-[10px] text-ink-light ${
                    col.sortable !== false ? 'cursor-pointer hover:text-ink transition-colors' : ''
                  } ${col.headerClassName || ''}`}
                  onClick={() => col.sortable !== false && requestSort(col.key)}
                >
                  <div className="flex items-center gap-2">
                    {col.label}
                    {col.sortable !== false && getSortIcon(col.key)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-faint font-mono">
            {sortedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-ink-light italic">
                  No data available
                </td>
              </tr>
            ) : (
              sortedData.map((row, idx) => (
                <tr
                  key={getRowKey(row, idx)}
                  onClick={() => onRowClick && onRowClick(row)}
                  className={`${onRowClick ? 'cursor-pointer' : ''} transition-colors ${
                    selectedRowKey === getRowKey(row, idx) ? 'bg-sage/10' : 'hover:bg-faint/30'
                  }`}
                >
                  {columns.map((col) => (
                    <td key={col.key} className={`px-4 py-3 ${col.className || ''}`}>
                      {col.render ? col.render(row) : (row as any)[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
