import logging

logger = logging.getLogger(__name__)

class CorsDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        
        # Log CORS-related headers for debugging
        if 'HTTP_ORIGIN' in request.META:
            logger.info(f"Request from origin: {request.META['HTTP_ORIGIN']}")
            logger.info(f"CORS headers in response: {[k for k in response if k.startswith('Access-Control-')]}")
            
            # Check if we're setting the right CORS headers
            if not response.has_header('Access-Control-Allow-Origin'):
                logger.warning(f"❌ No Access-Control-Allow-Origin header set for request from {request.META['HTTP_ORIGIN']}")
                # Add origin header for debugging purposes - remove in production
                response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
                response['Access-Control-Allow-Credentials'] = 'true'
                if request.method == 'OPTIONS':
                    response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
                    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                    logger.info("✅ Added missing CORS headers for OPTIONS preflight request")
            else:
                logger.info(f"✅ Access-Control-Allow-Origin is set to: {response['Access-Control-Allow-Origin']}")
        
        return response
