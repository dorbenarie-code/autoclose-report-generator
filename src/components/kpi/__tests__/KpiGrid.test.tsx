import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { KpiGrid } from '../KpiGrid';

const mockKpiData = {
  total_revenue: 1000000,
  average_income: 50000,
  total_reports: 150,
  crit_count: 5,
  open_tasks: 25,
  flag_rate: 12.5
};

describe('KpiGrid', () => {
  it('renders all KPI configurations correctly', () => {
    render(<KpiGrid data={mockKpiData} loading={false} error="" />);
    
    // Check if all KPI titles are rendered
    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('Average Income')).toBeInTheDocument();
    expect(screen.getByText('Total Reports')).toBeInTheDocument();
    expect(screen.getByText('Critical Alerts')).toBeInTheDocument();
    expect(screen.getByText('Open Tasks')).toBeInTheDocument();
    expect(screen.getByText('% with Flags')).toBeInTheDocument();

    // Check if values are formatted correctly
    expect(screen.getByText('$1,000,000')).toBeInTheDocument();
    expect(screen.getByText('$50,000')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('12.5%')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<KpiGrid data={null} loading={true} error="" />);
    expect(screen.getByTestId('loader')).toBeInTheDocument();
  });

  it('shows error state', () => {
    const errorMessage = 'Test error message';
    render(<KpiGrid data={null} loading={false} error={errorMessage} />);
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });
}); 