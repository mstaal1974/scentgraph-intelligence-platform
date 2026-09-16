# Scentprint

A Scentprint is a customer preference vector over the same dimensions as fragrance vectors: sensory qualities plus performance preferences. Input scores are validated on a 0–1 scale, normalised into a stable dimension order, and compared with candidate fragrance vectors using cosine similarity.

The foundation accepts explicit preference scores and returns a normalised vector plus ranked matches. Later versions may infer weights from liked/disliked fragrances, feedback, context, and confidence. Explanations should identify dominant shared dimensions without revealing proprietary model weights. Anonymous or consented identifiers, retention limits, deletion, and tenant isolation are required before production customer data is stored.
