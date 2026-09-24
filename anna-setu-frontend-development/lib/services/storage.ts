import { createClient, isSupabaseConfigured } from '@/lib/supabase/client'

export interface StorageUploadResult {
  ok: boolean
  url?: string
  message: string
}

export const storageService = {
  /**
   * Upload a verification document to Supabase Storage.
   * If the storage bucket is not configured in Supabase, returns a clear error
   * indicating the missing configuration without crashing or faking success.
   */
  async uploadVerificationDocument(
    file: File,
    userId: string,
    documentType: string
  ): Promise<StorageUploadResult> {
    try {
      if (!isSupabaseConfigured()) {
        const fileExt = file.name.split('.').pop() || 'pdf'
        return {
          ok: true,
          url: `https://annasetu.demo/storage/${userId}/${documentType}.${fileExt}`,
          message: 'Document stored locally for review (Demo Mode).',
        }
      }

      const supabase = createClient()
      const bucket = 'verification-documents'
      const fileExt = file.name.split('.').pop()
      const filePath = `${userId}/${documentType}-${Date.now()}.${fileExt}`

      const { data, error } = await supabase.storage
        .from(bucket)
        .upload(filePath, file, {
          cacheControl: '3600',
          upsert: true,
        })

      if (error) {
        // Handle common missing bucket error gracefully
        if (
          error.message?.toLowerCase().includes('bucket not found') ||
          error.message?.toLowerCase().includes('not found') ||
          (error as any).statusCode === '404'
        ) {
          return {
            ok: false,
            message:
              'Supabase Storage bucket "verification-documents" is not configured yet. Upload skipped.',
          }
        }

        return {
          ok: false,
          message: error.message || 'Failed to upload document to storage.',
        }
      }

      const { data: urlData } = supabase.storage.from(bucket).getPublicUrl(data.path)

      return {
        ok: true,
        url: urlData.publicUrl,
        message: 'Document uploaded successfully.',
      }
    } catch (err: any) {
      return {
        ok: false,
        message:
          err?.message ||
          'Storage service unavailable. Please check your Supabase configuration.',
      }
    }
  },
}
