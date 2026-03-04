interface MessageBubbleProps {
    content: string;
  }
  
  export default function MessageBubble({ content }: MessageBubbleProps) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl bg-primary px-4 py-3 text-primary-foreground">
          <p className="whitespace-pre-wrap break-words">{content}</p>
        </div>
      </div>
    );
  }