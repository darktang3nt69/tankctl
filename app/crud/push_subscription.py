from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.push_subscription import PushSubscription
from app.schemas.push_subscription import PushSubscriptionCreate, PushSubscriptionUpdate

def create_subscription(db: Session, subscription: PushSubscriptionCreate) -> PushSubscription:
    """Create a new push subscription"""
    db_subscription = PushSubscription(
        endpoint=subscription.endpoint,
        p256dh=subscription.p256dh,
        auth=subscription.auth,
        user_agent=subscription.user_agent,
        preferences=subscription.preferences
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

def get_subscription_by_endpoint(db: Session, endpoint: str) -> Optional[PushSubscription]:
    """Get a subscription by endpoint"""
    return db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()

def delete_subscription(db: Session, endpoint: str) -> bool:
    """Delete a subscription by endpoint"""
    subscription = get_subscription_by_endpoint(db, endpoint)
    if subscription:
        db.delete(subscription)
        db.commit()
        return True
    return False

def get_all_subscriptions(db: Session) -> List[PushSubscription]:
    """Get all push subscriptions"""
    return db.query(PushSubscription).all()

def update_subscription_preferences(db: Session, endpoint: str, preferences: Dict[str, Any]) -> Optional[PushSubscription]:
    """Update subscription preferences"""
    subscription = get_subscription_by_endpoint(db, endpoint)
    if subscription:
        subscription.preferences = preferences
        db.commit()
        db.refresh(subscription)
        return subscription
    return None 