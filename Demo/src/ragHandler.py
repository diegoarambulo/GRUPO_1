import faiss
from modelHandlers import ModelHandlers

SYSTEM_PROMPT = """
Eres un asistente técnico especializado en la plataforma SISAD (Sistema de Administración Documental).

INSTRUCCIONES:
- Responde ÚNICAMENTE basándote en el contexto proporcionado.
- Si el contexto no contiene suficiente información, indícalo claramente.
- Para código JSON o comandos, usa bloques de código con triple backtick.
- Sé preciso, claro y conciso.
- Responde siempre en español.
- Cita la fuente del documento cuando sea relevante.
"""

class RagHandlers:

    @staticmethod
    def retrieve(query: str, top_k: int = 5, min_score: float = 0.3):
        """
        Recupera los chunks más relevantes para una query.

        Args:
            query     : Pregunta del usuario
            top_k     : Número máximo de chunks a recuperar
            min_score : Umbral mínimo de similitud coseno (0-1)

        Returns:
            Lista de dicts con 'text', 'source' y 'score'
        """
        # ✅ Obtener modelos y archivos FAISS desde ModelHandlers
        embed_model = ModelHandlers.get_embed_model()
        index       = ModelHandlers.get_faiss_index()
        all_chunks  = ModelHandlers.get_faiss_chunks()

        # Embed la query
        q_emb = embed_model.encode([query]).astype('float32')
        faiss.normalize_L2(q_emb)

        # Buscar en FAISS
        scores, indices = index.search(q_emb, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= min_score and idx != -1:
                results.append({
                    'text':   all_chunks[idx].page_content,
                    'source': all_chunks[idx].metadata['source'],
                    'score':  float(score)
                })
        return results

    @staticmethod
    def rag_query(question: str, top_k: int = 5, verbose: bool = True) -> str:
        """
        Pipeline RAG completo con modelo local Qwen.
        """
        # ✅ Obtener modelo Qwen y tokenizer desde ModelHandlers
        model     = ModelHandlers.get_qwen_model()
        tokenizer = ModelHandlers.get_qwen_tokenizer()

        # ── 1. RETRIEVE ──
        chunks = RagHandlers.retrieve(question, top_k=top_k)

        if not chunks:
            return '⚠️ No se encontraron fragmentos relevantes en la documentación para responder esta pregunta.'

        if verbose:
            print(f'📦 {len(chunks)} chunks recuperados:')
            for i, c in enumerate(chunks):
                print(f'  [{i + 1}] score={c["score"]:.3f} | {c["source"]} | {c["text"][:80]}...')
            print()

        # ── 2. AUGMENT ──
        context_blocks = []
        for i, c in enumerate(chunks):
            context_blocks.append(
                f'[Fuente: {c["source"]} | Relevancia: {c["score"]:.2f}]\n{c["text"]}'
            )
        context = '\n\n---\n\n'.join(context_blocks)

        user_message = f'CONTEXTO DE LA DOCUMENTACIÓN SISAD:\n\n{context}\n\nPREGUNTA: {question}'

        # ── 3. GENERATE ──
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ]

        # Aplicar el chat template de Qwen
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=512,
            temperature=0.3,
            do_sample=True
        )

        # Extraer solo la respuesta generada (sin el prompt)
        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response