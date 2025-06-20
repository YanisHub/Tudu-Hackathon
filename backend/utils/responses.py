def api_response(success=True, message=None, data=None, status_code=None):
    """
    Fonction utilitaire pour standardiser les réponses API.
    
    Args:
        success (bool): Indique si l'opération a réussi
        message (str, optional): Message descriptif pour l'utilisateur
        data (any, optional): Les données à retourner
        status_code (int, optional): Le code de statut HTTP
        
    Returns:
        dict: Réponse formatée avec les champs success, message et data
    """
    response = {"success": success}
    
    if message is not None:
        response["message"] = message
        
    if data is not None:
        response["data"] = data
        
    return response, status_code