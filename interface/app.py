            st.markdown("### Documento Retido")
            st.markdown(f"**ID do Documento:** `{doc['documento_id']}`")
            st.markdown(f"**Tipo:** {doc['tipo_documento']}")
            st.markdown(f"**Prioridade:** {doc['nivel_prioridade']}")
            st.markdown(f"**Entrou na fila em:** {formatar_data(doc['data'])}")

            st.warning(f"**Motivo da Retenção para Auditoria:**\n{doc['justificativa_roteamento']}")

            score = doc["score_confianca_classificacao"]
            st.markdown(f"**Score de Confiança da Extração:** `{score * 100:.1f}%`")
            st.progress(score)

        # Coluna da direita: dados extraídos (somente leitura) e a decisão de quem revisa
        with col_dir:
            st.markdown("### Formulário de Revisão Clínica")

            with st.form(key=f"form_auditoria_{documento_id}"):
                st.caption("Dados extraídos pela IA, como a API os devolveu.")
                st.warning("Correção de dados será habilitada numa próxima versão")
                c_p1, c_p2 = st.columns([2, 1])
                with c_p1:
                    st.text_input("Nome do Paciente:", value=paciente.get("nome") or "", disabled=True, key=f"nome_{documento_id}")
                with c_p2:
                    st.text_input("Idade:", value=str(paciente.get("idade") or ""), disabled=True, key=f"idade_{documento_id}")

                c_m1, c_m2 = st.columns([2, 1])
                with c_m1:
                    st.text_input("Médico Solicitante:", value=medico.get("nome") or "", disabled=True, key=f"medico_{documento_id}")
                with c_m2:
                    st.text_input("CRM com UF:", value=medico.get("crm") or "", disabled=True, key=f"crm_{documento_id}")

                st.text_input(
                    "Diagnóstico Principal:", value=dados_ext.get("diagnostico_principal") or "", disabled=True, key=f"diag_{documento_id}"
                )
                st.text_input("CID-10 Sugerido:", value=dados_ext.get("cid_sugerido") or "", disabled=True, key=f"cid_{documento_id}")

                st.markdown("**Decisão de quem revisa:**")
                destino = st.radio("Encaminhar para:", list(DESTINOS_DA_DECISAO), horizontal=True, key=f"destino_{documento_id}")
                revisor = st.text_input("Nome de quem revisa (obrigatório):", max_chars=REVISOR_MAXIMO, key="nome_do_revisor")
                justificativa = st.text_area(
                    f"Justificativa (obrigatória, de {JUSTIFICATIVA_MINIMA} a {JUSTIFICATIVA_MAXIMA} caracteres):",
                    max_chars=JUSTIFICATIVA_MAXIMA,
                    key=f"justificativa_{documento_id}",
                )

                registrar = st.form_submit_button("✅ Registrar decisão", type="primary", width="stretch")

            if registrar:
                pendencia = validar_decisao(revisor, justificativa)
                if pendencia:
                    st.error(pendencia)
                else:
                    registrar_decisao(documento_id, destino, revisor, justificativa)


# ----------------------------------------------------------------------------
# ABA 3: HISTÓRICO & BUCKETS OCI
# ----------------------------------------------------------------------------
with tab_historico:
    st.subheader("📦 Histórico dos Documentos no Armazenamento")
    st.caption("Organização segregada de arquivos conforme exigido pelo edital Always Free da Oracle.")

    st.markdown("""
    <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;">
        <span style="background: #F1F5F9; border: 1px solid #CBD5E1; padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; color: #334155;">📥 <code>mediflow-recebidos</code> (Ingestão)</span>
        <span style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; color: #065F46;">✅ <code>mediflow-rotina</code> (Farmácia / PEP / Autorizações)</span>
        <span style="background: #FEF2F2; border: 1px solid #FECACA; padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; color: #991B1B;">🚨 <code>mediflow-urgentes</code> (Emergência)</span>
        <span style="background: #FFFBEB; border: 1px solid #FDE68A; padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; color: #92400E;">🔍 <code>mediflow-auditoria-humana</code> (Revisão Humana)</span>
        <span style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; color: #475569;">🚫 <code>mediflow-rejeitados</code> (Falhas / Rejeição)</span>
    </div>
    """, unsafe_allow_html=True)

    historico, erro_do_historico = ler(carregar_historico)
    if erro_do_historico:
        mostrar_erro(erro_do_historico)
    elif not historico:
        st.info("Nenhum documento no armazenamento ainda.")
    else:
        if len(historico) >= LIMITE_DA_API:
            st.caption(f"Os {LIMITE_DA_API} documentos mais recentes.")
        st.dataframe(
            [
                {
                    "Data": formatar_data(h["data"]),
                    "Documento": h["documento_id"],
                    "Status": h["status"],
                    "Prioridade": h["nivel_prioridade"],
                    "Destino": h["destino_principal"],
                    "Bucket": h["bucket"],
                }
                for h in historico
            ],
            width="stretch",
            hide_index=True,
        )


# ----------------------------------------------------------------------------
# CONTADORES DO TOPO: vêm da API, lidos depois de enviar ou decidir nesta execução
# ----------------------------------------------------------------------------
with area_dos_contadores:
    historico, _ = ler(carregar_historico)
    pendentes, _ = ler(carregar_pendentes)
    if historico is None or pendentes is None:
        st.warning("Contadores indisponíveis: a API não respondeu. O motivo aparece nas abas abaixo.")
    else:
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        with col_m1:
            st.metric(label="📄 Total de Documentos", value=len(historico))
        with col_m2:
            st.metric(label="⚠️ Fila de Revisão Humana", value=len(pendentes))
        with col_m3:
            st.metric(label="🚨 Emergências Médicas", value=sum(1 for h in historico if h["destino_principal"] == "Fila_Emergencia_Medica"))
        with col_m4:
            st.metric(label="✅ Rotina", value=sum(1 for h in historico if h["destino_principal"] in DESTINOS_DE_ROTINA))
        with col_m5:
            st.metric(label="🚫 Rejeitados", value=sum(1 for h in historico if h["status"] == "rejeitado"))

st.markdown("""
<div class="mediflow-footer">
    <div>
        <strong>🏥 MediFlow</strong> · Sistema Autônomo de Roteamento Clínico · <em>Hackathon ONE G10</em>
    </div>
    <div>
        <strong>Equipe:</strong> André · Ingrid · Guilherme · Lethicia | <strong>Infra:</strong> OCI VM Always Free & Object Storage
    </div>
</div>
""", unsafe_allow_html=True)
