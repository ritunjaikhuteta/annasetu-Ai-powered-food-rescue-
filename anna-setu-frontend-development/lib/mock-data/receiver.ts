/**
 * AnnaSetu — Receiver Mock Data
 */
import type { ReceiverData } from '@/lib/types/receiver'

export const RECEIVER_DATA: ReceiverData = {
  organizationName: 'Seva Community Kitchen',
  verified: true,
  openCapacity: 40,
  activeNeeds: [
    { id: 'need-1', mealPeriod: 'Lunch', foodType: 'Vegetarian', quantity: 20, requiredBy: 'Today, 8:00 PM', status: 'Matched' },
    { id: 'need-2', mealPeriod: 'Breakfast', foodType: 'Vegetarian', quantity: 25, requiredBy: 'Tomorrow, 8:00 AM', status: 'Open' },
  ],
  incomingDeliveries: [
    { id: 'delivery-1', donorName: 'Green Leaf Catering', foodName: 'Vegetarian Cooked Meals', quantity: 12, unit: 'kg', driverName: 'Arjun Sharma', status: 'Arriving', eta: 11 },
  ],
  receivedHistory: [
    { id: 'delivery-prev-1', donorName: 'Green Leaf Catering (C-Scheme)', foodName: 'Bakery Assortment & Bread', quantity: 18, unit: 'kg', driverName: 'Meena Kapoor', status: 'Received', arrivalTime: 'Yesterday, 7:15 PM' },
    { id: 'delivery-prev-2', donorName: 'ITC Rajputana, Jaipur', foodName: 'Cooked Rice, Dal & Mixed Veg', quantity: 35, unit: 'kg', driverName: 'Vikram Singh', status: 'Received', arrivalTime: '23 Sep, 1:45 PM' },
    { id: 'delivery-prev-3', donorName: 'Metro Banquet Hall, Mansarovar', foodName: 'Paneer Butter Masala & Rotis', quantity: 24, unit: 'kg', driverName: 'Arjun Sharma', status: 'Received', arrivalTime: '21 Sep, 9:20 PM' },
    { id: 'delivery-prev-4', donorName: 'Rawat Mishthan Bhandar, Jaipur', foodName: 'Packaged Snacks & Sweets', quantity: 15, unit: 'kg', driverName: 'Pooja Verma', status: 'Received', arrivalTime: '18 Sep, 4:10 PM' },
    { id: 'delivery-prev-5', donorName: 'The Forresta Bistro, Bani Park', foodName: 'Fresh Salads & Sandwiches', quantity: 12, unit: 'kg', driverName: 'Rajesh Kumar', status: 'Received', arrivalTime: '15 Sep, 2:30 PM' },
  ],
  impact: {
    mealsReceived: 185,
    totalQuantity: 580,
    deliveriesCompleted: 24,
    monthly: [
      { month: 'Apr', received: 45, meals: 135 },
      { month: 'May', received: 62, meals: 186 },
      { month: 'Jun', received: 78, meals: 234 },
      { month: 'Jul', received: 55, meals: 165 },
      { month: 'Aug', received: 92, meals: 276 },
      { month: 'Sep', received: 110, meals: 330 },
    ],
  },
}
