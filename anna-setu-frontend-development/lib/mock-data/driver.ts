/**
 * AnnaSetu — Driver Mock Data
 *
 * Mock delivery partner data aligned with canonical rescue scenario.
 */
import type { DriverData } from '@/lib/types/driver'

export const DRIVER_DATA: DriverData = {
  name: 'Arjun Sharma',
  verified: true,
  rating: 4.9,
  totalTrips: 84,
  vehicleType: 'Van (Insulated)',
  vehicleNumber: 'RJ 14 GC 4455',
  activeJob: {
    id: 'job-1042',
    donorName: 'Green Leaf Catering',
    pickupLocation: {
      address: 'Plot 14, Ashok Nagar, C-Scheme, Jaipur',
      city: 'Jaipur',
      state: 'Rajasthan',
      postalCode: '302001',
      lat: 26.9095,
      lng: 75.8016,
    },
    stops: [
      { order: 1, receiverName: 'Seva Community Kitchen', address: 'Sector 3, Malviya Nagar, Jaipur', quantity: 12, status: 'Completed' },
      { order: 2, receiverName: 'Anna Sadan Charitable Trust', address: 'Amrapali Marg, Vaishali Nagar, Jaipur', quantity: 8, status: 'In Progress' },
      { order: 3, receiverName: 'Sahara Community Home', address: 'Madhyam Marg, Mansarovar, Jaipur', quantity: 20, status: 'Pending' },
    ],
    totalDistance: 9.1,
    estimatedDuration: 35,
    estimatedEarnings: 264,
    foodDescription: 'Vegetarian Cooked Meals (Rice, Dal, Subzi)',
    quantity: 40,
    unit: 'kg',
    urgency: 'high',
    expiresAt: 'Today, 6:00 PM',
    status: 'In transit',
  },
  availableJobs: [
    {
      id: 'job-1045',
      donorName: 'Rajputana Heritage Banquets',
      pickupLocation: {
        address: 'Bhawani Singh Road, C-Scheme, Jaipur',
        city: 'Jaipur',
        state: 'Rajasthan',
        postalCode: '302005',
      },
      stops: [
        { order: 1, receiverName: 'Apna Ghar Shelter', address: 'Lane 4, Raja Park, Jaipur', quantity: 25, status: 'Pending' },
      ],
      totalDistance: 5.4,
      estimatedDuration: 20,
      estimatedEarnings: 280,
      foodDescription: 'Assorted Breads, Rotis, and Dry Curry',
      quantity: 25,
      unit: 'kg',
      urgency: 'medium',
      expiresAt: 'Today, 7:30 PM',
      status: 'Available',
    },
  ],
  earnings: {
    today: 264,
    thisWeek: 2850,
    thisMonth: 12400,
    totalPaid: 45600,
    pendingPayout: 1850,
    history: [
      { id: 'earn-1', deliveryId: 'AS-1041', amount: 320, date: 'Yesterday', status: 'Paid' },
      { id: 'earn-2', deliveryId: 'AS-1038', amount: 410, date: '18 Sep', status: 'Paid' },
      { id: 'earn-3', deliveryId: 'AS-1035', amount: 380, date: '17 Sep', status: 'Paid' },
    ],
  },
  completedDeliveries: [
    {
      id: 'job-1041',
      donorName: 'Green Leaf Catering',
      pickupLocation: {
        address: 'Plot 14, Ashok Nagar, C-Scheme, Jaipur',
        city: 'Jaipur',
        state: 'Rajasthan',
        postalCode: '302001',
      },
      stops: [
        { order: 1, receiverName: 'Seva Community Kitchen', address: 'Sector 3, Malviya Nagar, Jaipur', quantity: 18, status: 'Completed' },
      ],
      totalDistance: 6.2,
      estimatedDuration: 25,
      estimatedEarnings: 320,
      foodDescription: 'Bakery Assortment',
      quantity: 18,
      unit: 'kg',
      urgency: 'medium',
      expiresAt: 'Yesterday, 8:00 PM',
      status: 'Completed',
    },
  ],
}
