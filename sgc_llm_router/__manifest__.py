{
    'name': 'SGC LLM Router',
    'summary': 'Multi-provider LLM chat-completion routing with ordered fallback',
    'description': """
        Standalone provider config + fallback-chain scaffold. Not wired into
        any existing feature yet -- call sgc.llm.provider.chat_completion()
        from wherever a future caller needs a chat completion, and it will
        try each active provider in sequence order until one succeeds.

        Kept as its own module (depends on muk_mcp only for install
        ordering) so MuK IT's vendor module is never modified directly --
        their updates can't overwrite this.
    """,
    'version': '19.0.1.0.0',
    'category': 'Tools/API',
    'license': 'LGPL-3',
    'depends': ['base', 'muk_mcp'],
    'data': [
        'security/ir.model.access.csv',
        'views/llm_provider_views.xml',
        'data/llm_provider_data.xml',
    ],
    'installable': True,
    'application': False,
}
