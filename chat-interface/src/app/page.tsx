import { ChatInterface } from "@/components/chat-interface";
import { ProtectedWrapper } from "@/components/protected-wrapper";

export default function Home() {
  return (
    <ProtectedWrapper>
      <div className="flex-1 flex flex-col p-4">
        <ChatInterface />
      </div>
    </ProtectedWrapper>
  );
}
