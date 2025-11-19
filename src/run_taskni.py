"""
Script para rodar o servidor Taskni Core.

Similar ao run_service.py do toolkit, mas específico para o Taskni Core.
"""

import uvicorn

from taskni_core.core.settings import taskni_settings


def main():
    """Roda o servidor Taskni Core."""
    reload = taskni_settings.is_dev()

    print(f"🚀 Iniciando Taskni Core em {taskni_settings.HOST}:{taskni_settings.PORT}")
    print(f"📝 Modo: {'desenvolvimento' if reload else 'produção'}")
    print(f"🔗 Docs: http://{taskni_settings.HOST}:{taskni_settings.PORT}/docs")

    uvicorn.run(
        "taskni_core.main:app",
        host=taskni_settings.HOST,
        port=taskni_settings.PORT,
        reload=reload,
        log_level=taskni_settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
