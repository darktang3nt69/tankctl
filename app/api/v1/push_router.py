from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api.deps import get_current_user, get_db
from app.api.utils.responses import create_success_response, create_error_response
from app.schemas.push_subscription import PushSubscriptionCreate, PushSubscriptionUpdate, PushSubscription
from app.crud.push_subscription import create_subscription, get_subscription_by_endpoint, delete_subscription, update_subscription_preferences
from app.core.config import settings

router = APIRouter()

@router.post("/push/subscribe", response_model=PushSubscription)
async def subscribe_to_push_notifications(
    subscription: PushSubscriptionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Subscribe to push notifications.
    
    The frontend should call this endpoint with the PushSubscription object
    obtained from the browser's pushManager.subscribe() method.
    
    Example frontend code:
    ```javascript
    // Get VAPID public key
    const response = await fetch('/api/v1/push/vapid-public-key');
    const { data } = await response.json();
    const vapidPublicKey = data.vapidPublicKey;
    
    // Convert VAPID key to Uint8Array
    const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);
    
    // Register service worker
    const registration = await navigator.serviceWorker.register('/sw.js');
    
    // Subscribe to push notifications
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: convertedVapidKey
    });
    
    // Send subscription to server
    await fetch('/api/v1/push/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(subscription)
    });
    ```
    
    Notification types:
    - offline: Tank has gone offline
    - online: Tank has come back online
    - temperature_alert: Temperature is outside normal range
    - ph_alert: pH is outside normal range
    - command_completed: Command has been completed successfully
    - command_failed: Command execution failed
    
    Returns:
        PushSubscription: The created or existing subscription
    """
    # Check if subscription already exists
    existing = get_subscription_by_endpoint(db, subscription.endpoint)
    if existing:
        return create_success_response(data=existing)
    
    # Add user agent if not provided
    if not subscription.user_agent and "user-agent" in request.headers:
        subscription.user_agent = request.headers["user-agent"]
    
    # Create new subscription
    new_subscription = create_subscription(db, subscription)
    
    return create_success_response(
        data=new_subscription,
        status_code=status.HTTP_201_CREATED
    )

@router.delete("/push/unsubscribe")
async def unsubscribe_from_push_notifications(
    endpoint: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Unsubscribe from push notifications.
    
    The frontend should call this endpoint when a user unsubscribes
    or when the subscription is no longer valid.
    """
    success = delete_subscription(db, endpoint)
    
    if not success:
        return create_error_response(
            code="SUBSCRIPTION_NOT_FOUND",
            message="Subscription not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return create_success_response(
        data={"message": "Subscription deleted successfully"}
    )

@router.put("/push/preferences")
async def update_push_notification_preferences(
    endpoint: str,
    preferences: PushSubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update push notification preferences.
    
    The frontend can use this endpoint to update user preferences
    for different types of notifications.
    """
    updated = update_subscription_preferences(db, endpoint, preferences.preferences)
    
    if not updated:
        return create_error_response(
            code="SUBSCRIPTION_NOT_FOUND",
            message="Subscription not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return create_success_response(data=updated)

@router.get("/push/vapid-public-key")
async def get_vapid_public_key(current_user = Depends(get_current_user)):
    """
    Get the VAPID public key for push notifications.
    
    The frontend needs this key to subscribe to push notifications.
    """
    return create_success_response(
        data={"vapidPublicKey": settings.VAPID_PUBLIC_KEY}
    ) 