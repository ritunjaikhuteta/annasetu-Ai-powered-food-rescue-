/**
 * AnnaSetu — Admin Mock Data
 *
 * Operations command center data.
 */
import type { AdminData } from '@/lib/types/admin'

export const ADMIN_DATA: AdminData = {
  dashboard: {
    activeDonations: 12,
    openNeeds: 18,
    liveRoutes: 6,
    pendingVerifications: 4,
    healthyMatchRate: 94.2,
    dailyGoalKg: 250,
    dailyRescuedKg: 184,
    operationsQueue: [
      {
        id: 'op-1',
        type: 'verification',
        title: 'New Receiver Verification: Care India Trust',
        description: '3 documents submitted (NGO-DARPAN, PAN, 12A) awaiting review.',
        urgency: 'high',
        createdAt: '20 mins ago',
        entityId: 'rec-005',
      },
      {
        id: 'op-2',
        type: 'route_risk',
        title: 'ETA Delay Alert on Route AS-GL-0001',
        description: 'Arjun Sharma delayed by 8 mins due to Golf Course Road congestion. Food deadline safe.',
        urgency: 'medium',
        createdAt: '5 mins ago',
        entityId: 'AS-GL-0001',
      },
      {
        id: 'op-3',
        type: 'expiring_donation',
        title: 'Donation AS-1049 expiring in 45m',
        description: 'Grand Royale Hotel (15 kg Paneer Butter Masala) needs driver confirmation.',
        urgency: 'critical',
        createdAt: '12 mins ago',
        entityId: 'AS-1049',
      },
    ],
  },
  verificationQueue: [
    {
      id: 'ver-1',
      userId: 'usr-005',
      userName: 'Care India Trust',
      role: 'receiver',
      status: 'pending',
      documentsCount: 3,
      submittedAt: 'Today, 1:30 PM',
    },
    {
      id: 'ver-2',
      userId: 'usr-006',
      userName: 'Vikram Singh (Delivery)',
      role: 'driver',
      status: 'pending',
      documentsCount: 2,
      submittedAt: 'Today, 11:15 AM',
    },
    {
      id: 'ver-3',
      userId: 'usr-007',
      userName: 'Haldiram Foods - CP',
      role: 'donor',
      status: 'under_review',
      documentsCount: 4,
      submittedAt: 'Yesterday, 4:00 PM',
      assignedTo: 'Admin Priya',
    },
  ],
  recentActivity: [
    {
      id: 'act-1',
      type: 'delivery_handoff',
      description: 'Green Leaf Catering handed off 40kg food to Driver Arjun Sharma (OTP verified)',
      timestamp: '2:30 PM',
      actorName: 'Green Leaf Catering',
      entityId: 'AS-GL-0001',
    },
    {
      id: 'act-2',
      type: 'match_created',
      description: 'System matched AS-GL-0001 to 3 receivers (Seva Community, Anna Sadan, Sahara)',
      timestamp: '2:18 PM',
      actorName: 'AI Matching Engine',
      entityId: 'AS-GL-0001',
    },
    {
      id: 'act-3',
      type: 'donor_verified',
      description: 'Donor "Taj Banquets" approved and verified by Admin Priya',
      timestamp: '11:00 AM',
      actorName: 'Admin Priya',
      entityId: 'usr-002',
    },
  ],
}
