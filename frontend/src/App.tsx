import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { JuryDashboard } from './components/JuryDashboard';
import { ProductCard } from './components/ProductCard';
import { PurchaseModal } from './components/PurchaseModal';
import { OrderTimeline } from './components/OrderTimeline';
import { ServiceStatusPanel } from './components/ServiceStatusPanel';
import { EventLogViewer } from './components/EventLogViewer';
import {
  fetchProducts,
  fetchInventory,
  fetchSimulationStatus,
  fetchRecentEvents,
  fetchOrder
} from './services/api';
import { Product, Inventory, SystemStatus, OutboxEvent, Order } from './types';

export function App() {
  const [product, setProduct] = useState<Product | null>(null);
  const [inventory, setInventory] = useState<Inventory | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [events, setEvents] = useState<OutboxEvent[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [isBuyModalOpen, setIsBuyModalOpen] = useState(false);

  const refreshAllData = async () => {
    try {
      const [prods, statusRes, evts] = await Promise.all([
        fetchProducts(),
        fetchSimulationStatus(),
        fetchRecentEvents(),
      ]);

      if (prods.length > 0) {
        setProduct(prods[0]);
        const invRes = await fetchInventory(prods[0].product_id);
        setInventory(invRes);
      }
      setStatus(statusRes);
      setEvents(evts);
    } catch (e) {
      console.error('Data polling error:', e);
    }
  };

  useEffect(() => {
    refreshAllData();
    const interval = setInterval(refreshAllData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleOrderCreated = (order: Order) => {
    setSelectedOrder(order);
    refreshAllData();
  };

  const handleSelectOrder = async (orderId: string) => {
    try {
      const ord = await fetchOrder(orderId);
      setSelectedOrder(ord);
    } catch (e) {
      console.error('Order fetch error:', e);
    }
  };

  return (
    <div className="min-h-screen pb-12 font-sans bg-[#090d16] text-slate-100">
      <Navbar status={status} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 space-y-6">
        {/* JURY DEMO CORE CONTROL PANEL */}
        <JuryDashboard
          status={status}
          onRefresh={refreshAllData}
          onSelectOrder={handleSelectOrder}
        />

        {/* FLASH SALE PRODUCT CARD */}
        <ProductCard
          product={product}
          inventory={inventory}
          onOpenBuyModal={() => setIsBuyModalOpen(true)}
        />

        {/* ORDER STATE MACHINE TIMELINE */}
        <OrderTimeline order={selectedOrder} />

        {/* INFRASTRUCTURE MATRIX & EVENT LOG */}
        <div className="grid grid-cols-1 gap-6">
          <ServiceStatusPanel status={status} />
          <EventLogViewer events={events} />
        </div>
      </main>

      {/* PURCHASE MODAL */}
      <PurchaseModal
        isOpen={isBuyModalOpen}
        onClose={() => setIsBuyModalOpen(false)}
        onOrderCreated={handleOrderCreated}
      />
    </div>
  );
}

export default App;
